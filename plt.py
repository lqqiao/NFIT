from vcdvcd import VCDVCD
import os
import csv
import numpy as np
import time
import re

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

def compare_vcd_files_analysis(fi_mode, proj_dir, pulse_width, sim_time):
    fl_wave = os.path.join(proj_dir, "fault_data", "fault_wave", "fl_wave.vcd")
    
    # 读取文件，提取第一列并去重（保留顺序）
    perfect_fi_signal_path = os.path.join(proj_dir, "perfect_fi_signal.txt")
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

    # 定义新的CSV文件路径
    reliability_csv_path = os.path.join(proj_dir, "fault_data", "fault_wave", "reliability_results.csv")

    # 在循环开始前创建CSV文件并写入表头
    with open(reliability_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["fi_num", "Reliability"])

    fault_num = 0
    sum = 0
    i = 0
    signal_record_path = os.path.join(proj_dir, "signal_record.txt")
    if (fi_mode == "ISMC"):
        rate = pulse_width / (sim_time * 1000)
    elif (fi_mode == "MC"):
        rate = 1
    else:
        print(f"no support this mode: {fi_mode}")
    with open(signal_record_path, 'r') as file:
        for current_line_num, line in enumerate(file, 1):
            sig = line.rstrip('\n')
            signal_a_time = get_value_at_time(signal_a_data, sim_time * 1000 * (i+1) - 1)
            signal_b_time = get_value_at_time(signal_b_data, sim_time * 1000 * (i+1) - 1)
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
        
            timestamp = time.localtime()
            formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", timestamp)
            Reliability = 1 - fault_num / sum * rate

            # 将可靠性结果追加到新的CSV文件中
            with open(reliability_csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([i, Reliability])
            print(f"[{formatted_time}]\t{Reliability}")
            


if __name__ == "__main__":
    proj_dir = "D://doctor_data//paper_data//monte_carlo//c3540//original"
    pulse_width = 100
    sim_time = 10
    fi_mode = "ISMC"
    compare_vcd_files_analysis(fi_mode, proj_dir, pulse_width, sim_time)