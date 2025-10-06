import re
import os
from filter import parse_verilog

#################################################
#
#   输入：待解析的文件路径，输出文件路径
#   输出内容：该文件的例化层次
#   输出格式：[该文件的顶层模块名称] [被例化的模块名字] [被例化的模块实际名字]
#   输出示例：top u_calculate calculte
#   要求：不允许该文件内同时存在两个module
#
#################################################
def parse_ast_instance(filepath, output_file_path):
    module_pattern = re.compile(r'ModuleDef: (\w+)')
    instance_pattern = re.compile(r'Instance:\s+([\w_]+),\s*([\w_]+)')
    
    hierarchy = []

    with open(filepath, 'r') as f:
        for line in f:
            module_match = module_pattern.search(line)
            if module_match:
                mod_name = module_match.group(1)
            instance_match = instance_pattern.search(line)
            if instance_match:
                hierarchy.append({
                    "mod_name": mod_name,
                    "instance_name": instance_match.group(1),
                    "instance_mod_name": instance_match.group(2)
                })

    with open(output_file_path, 'a', encoding='utf-8') as txtfile:
        for _, instance in enumerate(hierarchy, 1):
            txtfile.write(f"{instance['mod_name']} {instance['instance_name']} {instance['instance_mod_name']}\n")


#####################################################################
#
#   描述：给定dut文件，输出该文件的例化模块
#   
#   具体功能：
#   1、生成ast语法树
#   2、解析语法树，提取例化信息
#   
#   限制：
#   2、不支持sv文件
#
####################################################################
def extract_dut_hierarchy(filepath, output_dir):
    parse_verilog(filepath)         # 生成ast语法树

    ast_output_path = os.path.join(output_dir, 'ast_output.txt')
    if os.path.exists(ast_output_path):
        os.remove(ast_output_path)
    os.replace('ast_output.txt', ast_output_path)

    hierarchy_file_path = os.path.join(output_dir, 'hier.txt')
    parse_ast_instance(ast_output_path, hierarchy_file_path)        # 提取例化信息

    os.remove('parser.out')
    os.remove('parsetab.py')


if __name__ == "__main__":
    top_module = "c17_tb"  # 顶层模块名称
    verilog_file = f"{top_module}.v"  # 顶层模块文件
    output_file = "hierarchy_output.txt"