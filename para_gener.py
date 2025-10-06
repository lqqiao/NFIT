import re
import os
import hierarchy as hier
import shutil
from filter import extract_dut_signal
from fi_class import dut
from collections import defaultdict
import argparse


############################################################
#
#   输入：层次结构文件hierarchy.txt和每个模块的信号文件
#   输出：用于故障注入的信号文件
#   输出格式（示例）：c17_tb/c17_inst/N10
#
#############################################################
def combine_hier_sig(hier_file_path, sig_file_path, fi_sig_file_path):
    with open(hier_file_path, 'r') as hier_file:
        for line in hier_file:
            hier_parts = line.strip().split()
            with open(sig_file_path, 'r') as sig_file:
                for sig_line in sig_file:
                    sig_parts = sig_line.strip().split()
                    print(f"hier_parts[1] = {hier_parts[1]}, sig_parts[0] = {sig_parts[0]}")
                    if(hier_parts[1] == sig_parts[0]):
                        with open(fi_sig_file_path, 'a') as f:
                            fi_signal = f"{hier_parts[0]}/{sig_parts[1]}\n"
                            f.write(fi_signal)


###########################################################
#
#   描述：将生成的临时文件hier.txt转换为层次结构清晰的文件
#   补充：此段代码由deepseek生成
#
###########################################################
def combine_proj_hier(tmp_dir, proj_dir):
    input_file = os.path.join(tmp_dir, "hier.txt")
    output_file = os.path.join(tmp_dir, "hierarchy.txt")

    # 读取输入文件
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    # 构建父子关系映射
    parent_map = defaultdict(list)
    child_map = {}
    
    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            continue
        parent, instance, child = parts[0], parts[1], parts[2]
        parent_map[parent].append((instance, child))
        child_map[child] = parent
    
    # 找到所有根节点(没有被其他模块实例化的模块)
    roots = set(parent_map.keys()) - set(child_map.keys())
    
    # 递归生成路径
    def generate_paths(node, current_path):
        paths = []
        for instance, child in parent_map.get(node, []):
            new_path = f"{current_path}/{instance}" if current_path else instance
            paths.append(f"{root}/{new_path} {child}")
            paths.extend(generate_paths(child, new_path))
        return paths
    
    # 为每个根节点生成路径
    all_paths = []
    for root in roots:
        all_paths.extend(generate_paths(root, ""))
    
    # 写入输出文件
    with open(output_file, 'w') as f:
        for path in sorted(all_paths):
            f.write(path + '\n')


def add_sig_width(fi_sig_file, modelsim_fi_sig_file, perfect_fi_sig_file):
    with open(fi_sig_file, 'r') as f:
        for line in f:
            fi_sig_str = line.strip()
            count = 0
            with open(modelsim_fi_sig_file, 'r') as mf:
                for ml in mf:
                    count += ml.count(fi_sig_str + ' ')
                    count += ml.count(fi_sig_str + '[')
                    if (count > 1):
                        for i in range(count-1):
                            with open(perfect_fi_sig_file, 'a') as pf:
                                string = f"{fi_sig_str} {i} {count - 1}\n"
                                pf.write(string)
                    else:
                        with open(perfect_fi_sig_file, 'a') as pf:
                            string = f"{fi_sig_str} {count - 1} {count}\n"
                            pf.write(string)


#############################################################
#
#   输入：dut文件和testbench模板、故障注入类型
#   输出：用于故障注入的信号，用层次结构表示
#   具体功能：
#   1、提取每个模块的信号，区分reg和wire类型信号，输出到reg.txt和wire.txt文件中
#   2、提取整个工程的层次结构，输出到hierarchy_output.txt文件中
#   3、依据testbench模板，给每个输入向量组合生成testbench文件，用于对不同输入向量进行故障注入试验
#
##############################################################
def fault_injection_parameter_generation():
    dut_dir = os.path.join(dut.proj_dir, "dut")
    tmp_dir = os.path.join(dut.proj_dir, "tmp")
    
    if not os.path.exists(dut_dir):
        print("# 该工程下的dut目录不存在，无法进行词法分析")
        return False
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir, exist_ok=True)

    # 提取dut信号
    for root, dirs, files in os.walk(dut_dir):
        for file in files:
            file_path = os.path.join(root, file)
            extract_dut_signal(file_path , tmp_dir)

    wire_signal_file_path = os.path.join(tmp_dir, "wires.txt")
    perfect_fi_sig_file_path = os.path.join(dut.proj_dir, "perfect_fi_signal.txt")
    if os.path.exists(perfect_fi_sig_file_path):
        os.remove(perfect_fi_sig_file_path)

    with open(wire_signal_file_path, 'r') as wire_file:
        for line in wire_file:
            hier_parts = line.strip().split()
            with open(perfect_fi_sig_file_path, 'a') as f:
                fi_signal = f"{hier_parts[0]}/{hier_parts[1]} {int(hier_parts[2])-1} {hier_parts[2]}\n"
                f.write(fi_signal)
    print("fault injection parameters generation is done!\n")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--proj_dir', type=str, required=True, help="dut project directory")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    dut.proj_dir = args.proj_dir
    fault_injection_parameter_generation()