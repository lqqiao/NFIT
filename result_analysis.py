import vcdvcd
import os
import re
import numpy as np
import time
from fi_class import dut, injector
from vcd_compare import VCDComparator
from vcdvcd import VCDVCD

def compare_bits(bin1, bin2):
    # 去除高位无效零，找到第一个'1'的位置
    def trim_leading_zeros(b):
        b = b.lstrip('0')  # 去除所有前导零
        return b if b else '0'  # 如果全零则保留一个'0'
    
    # 获取有效部分
    valid1 = trim_leading_zeros(bin1)
    valid2 = trim_leading_zeros(bin2)
    
    # 补齐较短的有效部分
    max_len = max(len(valid1), len(valid2))
    padded1 = valid1.zfill(max_len)
    padded2 = valid2.zfill(max_len)
    
    # 逐位比较（从最低位开始编号）
    differences = []
    for i in range(max_len):
        if padded1[i] != padded2[i]:
            bit_pos = i  # 位置从最低有效位开始编号
            differences.append(bit_pos)
    
    return sorted(differences)


def save_fault_stats_to_txt(stats, filename="fault_stats.txt"):
    bit_width = stats["bit_width"]
    fi_num = stats["fi_num"]
    bit_errors = stats["bit_errors"]
    
    with open(filename, 'w') as file:
        # 写入表头（对齐格式）
        file.write(f"{'Bit位号':<10}{'错误次数':<10}{'注入次数':<10}{'错误率':<10}\n")
        file.write("-" * 40 + "\n")
        
        # 逐位写入数据
        for bit in range(bit_width):
            error_count = bit_errors[bit]
            error_rate = error_count / fi_num if fi_num > 0 else 0.0
            file.write(f"{bit:<10}{error_count:<10}{fi_num:<10}{error_rate:.4f}\n")
    
    print(f"输出信号的数据已保存到 {filename}")

def save_signal_stats_to_txt_seq_ismc(signal_stats, signals, fault_num, inject_sum, rate, filename="signal_stats.txt"):
    dff_fault_num = 0
    gate_fault_num = 0
    for signal in signals:
        stats = signal_stats[signal]
        fault_count = stats["fault_count"]
        
        # 计算当前信号的ser并添加到列表
        if stats["signal_type"] == "dff":
            dff_fault_num += fault_count
        else:
            gate_fault_num += fault_count
        
    
    # 计算所有信号ser的平均值
    avg_ser = (gate_fault_num * rate + dff_fault_num) / inject_sum

    with open(filename, "w") as f:
        # 写入每个信号的数据
        f.write(f"all\t{fault_num}\t{inject_sum}\t{avg_ser}\n")

        for signal in signals:
            stats = signal_stats[signal]
            fault_count = stats["fault_count"]
            inject_count = stats["inject_count"]
            if stats["signal_type"] == "dff" :
                ser = fault_count / inject_count
            else:
                ser = fault_count / inject_count * rate if inject_count > 0 else 0.0

            
            # 格式：信号名\t错误次数\t注入次数\t软错误率
            f.write(f"{signal}\t{fault_count}\t{inject_count}\t{ser}\n")
    
    print(f"注入信号的数据已保存到 {filename}")
    return avg_ser

def save_signal_stats_to_txt(signal_stats, signals, fault_num, sum, rate, filename="signal_stats.txt"):
    with open(filename, "w") as f:
        # 写入每个信号的数据
        f.write(f"all\t{fault_num}\t{sum}\t{fault_num / sum * rate}\n")

        for signal in signals:
            stats = signal_stats[signal]
            fault_count = stats["fault_count"]
            inject_count = stats["inject_count"]
            ser = fault_count / inject_count * rate if inject_count > 0 else 0.0
            
            # 格式：信号名\t错误次数\t注入次数\t软错误率
            f.write(f"{signal}\t{fault_count}\t{inject_count}\t{ser}\n")
    
    print(f"注入信号的数据已保存到 {filename}")


def compare_vcd_files(fi_mode):
    fl_wave = os.path.join(dut.proj_dir, "fault_data", "fault_wave", "fl_wave.vcd")
    
    # 读取文件，提取第一列并去重（保留顺序）
    perfect_fi_signal_path = os.path.join(dut.proj_dir, "perfect_fi_signal.txt")
    with open(perfect_fi_signal_path, "r") as f:
        signals = []
        seen = set()
        for line in f:
            if line.strip():  # 跳过空行
                signal = line.split()[0]  # 提取第一列（信号名称）
                signalIndex = line.split()[1]  # 提取第二列（信号索引）
                width = line.split()[2]  # 提取第三列（信号位宽）
                if width != "1":
                    signal = f"{signal}[{signalIndex}]"
                if signal not in seen:
                    seen.add(signal)
                    signals.append(signal)
    
    signal_stats = {
        signal: {"fault_count": 0, "inject_count": 0}
        for signal in signals
    }

    print("# 开始分析注入结果")
    vcd_fl = VCDVCD(fl_wave)
    print(vcd_fl.signals)
    signal_a_name = vcd_fl.signals[0]
    signal_b_name = vcd_fl.signals[1]
    signal_a_data = vcd_fl[signal_a_name].tv
    signal_b_data = vcd_fl[signal_b_name].tv

    match = re.search(r'\[(\d+):(\d+)\]', signal_a_name)
    if match:
        msb, lsb = int(match.group(1)), int(match.group(2))
        bit_width = msb - lsb + 1
    else:
        bit_width = 1
    
    output_fault_stats = {
        "signal_name": "output_signal",
        "bit_width": bit_width,
        "fi_num": 0,
        "bit_errors": np.zeros(bit_width, dtype=int),
    }

    fault_num = 0
    sum = 0
    i = 0
    signal_record_path = os.path.join(dut.proj_dir, "signal_record.txt")
    with open(signal_record_path, 'r') as file:
        for current_line_num, line in enumerate(file, 1):
            sig = line.rstrip('\n')
            signal_a_time = get_value_at_time(signal_a_data, injector.sim_time * 1000 * (i+1) - 1)
            signal_b_time = get_value_at_time(signal_b_data, injector.sim_time * 1000 * (i+1) - 1)
            if signal_a_time != signal_b_time:
                signal_stats[sig]["fault_count"] += 1
                fault_num += 1
                print(f"# 结果分析：第{i}次故障注入的结果：注入波形与黄金波形不一致")
                diff = compare_bits(signal_a_time, signal_b_time)
                for output_signal in diff:
                    output_fault_stats["bit_errors"][output_signal] += 1
            else:
                print(f"# 结果分析：第{i}次故障注入的结果：注入波形与黄金波形一致")
            signal_stats[sig]["inject_count"] += 1
            sum += 1
            i += 1


    # 结果保存
    if (fi_mode == "ISMC"):
        rate = injector.pulse_width / (injector.sim_time * 1000)
    elif (fi_mode == "MC"):
        rate = 1
    else:
        print(f"no support this mode: {fi_mode}")
    signal_result_path = os.path.join(dut.proj_dir, "signal_result.txt")
    save_signal_stats_to_txt(signal_stats, signals, fault_num, sum, rate, signal_result_path)

    output_fault_stats["fi_num"] = sum
    output_signal_result_path = os.path.join(dut.proj_dir, "output_signal_result.txt")
    save_fault_stats_to_txt(output_fault_stats, output_signal_result_path)

    timestamp = time.localtime()
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", timestamp)
    # print(f"[{formatted_time}]\tReliability = {1 - fault_num / sum * rate}")
    print(f"[{formatted_time}]\tReliability = {1 - (fault_num * 2) / (sum * 3) * rate}")


def compare_seq_vcd_files(fi_mode):
    fl_wave = os.path.join(dut.proj_dir, "fault_data", "fault_wave", "fl_wave.vcd")
    
    # 读取文件，提取第一列并去重（保留顺序）
    perfect_fi_signal_path = os.path.join(dut.proj_dir, "perfect_fi_signal.txt")
    with open(perfect_fi_signal_path, "r") as f:
        signals = []
        seen = set()
        for line in f:
            if line.strip():  # 跳过空行
                signal = line.split()[0]  # 提取第一列（信号名称）
                signalIndex = line.split()[1]  # 提取第二列（信号索引）
                width = line.split()[2]  # 提取第三列（信号位宽）
                if width != "1":
                    signal = f"{signal}[{signalIndex}]"
                if signal not in seen:
                    seen.add(signal)
                    signals.append(signal)
    
    signal_stats = {
        signal: {"fault_count": 0, "inject_count": 0, "signal_type": "gate"}
        for signal in signals
    }

    print("# 开始分析注入结果")
    vcd_fl = VCDVCD(fl_wave)
    print(vcd_fl.signals)
    signal_a_name = vcd_fl.signals[0]
    signal_b_name = vcd_fl.signals[1]
    signal_a_data = vcd_fl[signal_a_name].tv
    signal_b_data = vcd_fl[signal_b_name].tv

    match = re.search(r'\[(\d+):(\d+)\]', signal_a_name)
    if match:
        msb, lsb = int(match.group(1)), int(match.group(2))
        bit_width = msb - lsb + 1
    else:
        bit_width = 1
    
    output_fault_stats = {
        "signal_name": "output_signal",
        "bit_width": bit_width,
        "fi_num": 0,
        "bit_errors": np.zeros(bit_width, dtype=int),
    }

    fault_num = 0
    sum = 0
    i = 0
    signal_record_path = os.path.join(dut.proj_dir, "signal_record.txt")
    with open(signal_record_path, 'r') as file:
        for current_line_num, line in enumerate(file, 1):
            cleaned_line = line.rstrip('\n').strip() 
            if not cleaned_line:
                continue
            parts = cleaned_line.split()
            
            if len(parts) == 2:
                sig, signal_type = parts
                if signal_type == "dff":
                    signal_stats[sig]["signal_type"] = "dff"
            else:
                print(f"Warning: Line {current_line_num} has invalid format - {cleaned_line}")
                return
            flag = 0
            signal_a_time = get_value_at_time(signal_a_data, injector.sim_time * 1000 * i + injector.period * 1000 - 1)
            signal_b_time = get_value_at_time(signal_b_data, injector.sim_time * 1000 * i + injector.period * 1000 - 1)
            if signal_a_time != signal_b_time:
                print(f"# Error：第{i}次故障注入的结果：复位波形不一致")
                break
            for j in range(injector.dff_num):
                signal_a_time = get_value_at_time(signal_a_data, injector.sim_time * 1000 * i + injector.period * (injector.dff_num + j + 2) * 1000 - 1)
                signal_b_time = get_value_at_time(signal_b_data, injector.sim_time * 1000 * i + injector.period * (injector.dff_num + j + 2) * 1000 - 1)
                if signal_a_time != signal_b_time:
                    signal_stats[sig]["fault_count"] += 1
                    fault_num += 1
                    print(f"# 结果分析：第{i}次故障注入的结果：在注入故障后的第{j+1}个周期检测到故障，注入波形与黄金波形不一致")
                    diff = compare_bits(signal_a_time, signal_b_time)
                    if fi_mode == "MC":
                        for output_signal in diff:
                            output_fault_stats["bit_errors"][output_signal] += 1
                    else:
                        if signal_type == "gate":
                            for output_signal in diff:
                                scale_value = 1 * (injector.pulse_width / (injector.period * 1000))
                                output_fault_stats["bit_errors"][output_signal] += scale_value
                        else:
                            for output_signal in diff:
                                output_fault_stats["bit_errors"][output_signal] += 1
                    flag = 1
                    break
            if flag == 0:
                print(f"# 结果分析：第{i}次故障注入的结果：注入波形与黄金波形一致")
            signal_stats[sig]["inject_count"] += 1
            sum += 1
            i += 1


    # 结果保存
    if (fi_mode == "ISMC"):
        rate = injector.pulse_width / (injector.period * 1000)
        signal_result_path = os.path.join(dut.proj_dir, "signal_result.txt")
        avg_ser = save_signal_stats_to_txt_seq_ismc(signal_stats, signals, fault_num, sum, rate, signal_result_path)

        output_fault_stats["fi_num"] = sum
        output_signal_result_path = os.path.join(dut.proj_dir, "output_signal_result.txt")
        save_fault_stats_to_txt(output_fault_stats, output_signal_result_path)

        timestamp = time.localtime()
        formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", timestamp)
        print(f"[{formatted_time}]\tReliability = {1 - avg_ser}")
    elif (fi_mode == "MC"):
        rate = 1
        signal_result_path = os.path.join(dut.proj_dir, "signal_result.txt")
        save_signal_stats_to_txt(signal_stats, signals, fault_num, sum, rate, signal_result_path)

        output_fault_stats["fi_num"] = sum
        output_signal_result_path = os.path.join(dut.proj_dir, "output_signal_result.txt")
        save_fault_stats_to_txt(output_fault_stats, output_signal_result_path)

        timestamp = time.localtime()
        formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", timestamp)
        print(f"[{formatted_time}]\tReliability = {1 - fault_num / sum * rate}")
    else:
        print(f"no support this mode: {fi_mode}")



def get_value_at_time(tv, time):
    # 确保tv是排序好的（通常VCD数据已经是按时间排序的）
    low = 0
    high = len(tv) - 1
    best_index = 0
    
    while low <= high:
        mid = (low + high) // 2
        t, v = tv[mid]
        if t < time:
            best_index = mid
            low = mid + 1
        elif t > time:
            high = mid - 1
        else:
            return v
    
    return tv[best_index][1] if best_index < len(tv) else None

if __name__ == "__main__":
    # 定义两个 VCD 文件路径
    file1 = "D://doctor_data//test//golden_data//golden_wave//golden_wave_0.vcd"
    file2 = "D://doctor_data//test//fault_data//0//fault_wave//0_fault_wave_0.vcd"

    # 设置时间容差（可选）
    tolerance = 0  # 单位为时间单位（如 ns）

    # 比较两个波形文件
    result = compare_vcd_files(file1, file2, tolerance)
    if (result == True):
        print("没有故障")
    else:
        print("有故障")
