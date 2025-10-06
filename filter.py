from __future__ import absolute_import
from __future__ import print_function
import os
from pyverilog.vparser.parser import parse
import re
import tempfile
from collections import defaultdict

class TreeNode:
    """基础树节点类"""
    def __init__(self, value, children=None):
        self.value = value
        self.children = children if children is not None else []
    
    def add_child(self, node):
        self.children.append(node)

class ASTTraverser:
    """通用的抽象语法树(AST)遍历器"""
    
    def __init__(self, visit_methods=None):
        """
        初始化遍历器
        
        Args:
            visit_methods: 自定义访问方法的字典，格式为 {节点类型: 处理函数}
        """
        self.current_node = None  # 当前正在处理的节点
    
    def traverse(self, node):
        """
        遍历AST节点
        
        Args:
            node: 要遍历的AST节点
        
        Returns:
            处理结果，取决于具体的访问方法
        """
        self.current_node = node
        
        # 获取节点类型
        node_type = type(node).__name__
        attrstr = ""
        if self.current_node.attr_names:
            nvlist = [getattr(self.current_node, n) for n in self.current_node.attr_names]
            attrstr = ', '.join('%s' % v for v in nvlist)
        if (node_type == "ModuleDef" and attrstr != "dff"):
            print(f"{node_type}: {attrstr}")
            for child in self.current_node.children():
                self.traverse(child)
        
        for child in self.current_node.children():
            self.traverse(child)
    

def preprocess_trireg_to_reg(content):
    return re.sub(r"\btrireg\b", "reg", content, flags=re.MULTILINE)

def parse_verilog(filepath):
    # 读取并预处理
    with open(filepath, 'r', encoding='utf-8') as f:
        content = preprocess_trireg_to_reg(f.read())
        
        # 通过临时文件解析
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.v') as f:
        f.write(content)
        temp_path = f.name

    # 直接传递硬编码参数到parse函数
    ast, _ = parse([temp_path]) #函数要求输入是list，后续可以扩展功能

    # 直接传递文件对象给ast.show()的buf参数
    with open("ast_output.txt", "w") as f:
        ast.show(buf=f)

    # 创建遍历器并遍历AST
    traverser = ASTTraverser()
    print(traverser.traverse(ast))



# 在 parse_ast_output 函数中
def parse_ast_output(filepath):
    # 新增端口声明匹配模式
    port_pattern = re.compile(r'Port: (\w+),')
    # 新增模块匹配模式
    module_pattern = re.compile(r'ModuleDef: (\w+)')
    decl_pattern = re.compile(r'(Input|Output|Inout|Wire|Reg):\s+([\w,]+),') 
    width_pattern = re.compile(r'IntConst:\s+(\d+)')

    # 修改模块存储结构为字典
    modules = {}  # 原先是列表，改为字典存储
    current_module = None
    
    with open(filepath, 'r') as f:
        for line in f:
            module_match = module_pattern.search(line)
            if module_match:
                mod_name = module_match.group(1)
                current_module = {
                    'name': mod_name,
                    'variables': {}
                }
                modules[mod_name] = current_module  # 使用模块名作为key
                current_var = None
                width_buffer = []
                current_declaration = False  # 新增声明状态标记
                continue

            # 在变量声明开始时设置标记
            decl_match = decl_pattern.search(line)
            if decl_match and current_module:
                current_declaration = True  # 标记进入声明区域
                var_type, vars_str = decl_match.groups()
                var_names = [v.strip() for v in vars_str.split(',')]

                for var_name in var_names:                    
                    # 自动创建变量记录（如果不存在）
                    if var_name not in current_module['variables']:
                        current_module['variables'][var_name] = {
                            'port': 'internal',
                            'var_type': None,
                            'width': 1,  # 新增默认位宽
                            'msb': 0,    # 新增默认值
                            'lsb': 0     # 新增默认值
                        }
                    
                    # 更新端口类型（新增Inout处理）
                    if var_type in ('Input', 'Output', 'Inout'):
                        current_module['variables'][var_name]['port'] = var_type.lower()
                    else:
                        if not current_module['variables'][var_name]['var_type']:
                            current_module['variables'][var_name]['var_type'] = var_type
                # 新增声明结束检测
                if ')' in line and current_declaration:
                    current_declaration = False
                    current_var = None  # 清除当前变量引用
                # 收集位宽信息（保持现有逻辑，但作用域限定在当前变量）
                # 修改位宽收集条件：只在声明区域内处理
                width_match = width_pattern.search(line)
                if width_match and current_declaration and current_var:  # 三重验证
                    # 原有收集逻辑保持不变
                    if 'width_values' not in current_module['variables'][current_var]:
                        current_module['variables'][current_var]['width_values'] = []
                    current_module['variables'][current_var]['width_values'].append(int(width_match.group(1)))
                
                # 当检测到声明结束符号时处理位宽（保持现有逻辑）
                if ')' in line:
                    for var_name in var_names:
                        values = current_module['variables'][var_name].get('width_values', [])
                        if len(values) >= 2:
                            msb, lsb = values[-2], values[-1]
                            current_module['variables'][var_name]['width'] = msb - lsb + 1
                            current_module['variables'][var_name]['msb'] = msb
                            current_module['variables'][var_name]['lsb'] = lsb
                        elif len(values) == 1:
                            current_module['variables'][var_name]['width'] = values[0] + 1
                            current_module['variables'][var_name]['msb'] = values[0]
                            current_module['variables'][var_name]['lsb'] = 0
                        current_module['variables'][var_name]['width_values'] = []
            
            if current_module and current_var and width_buffer:
                if len(width_buffer) >= 2:
                    msb, lsb = width_buffer[-2], width_buffer[-1]  # 取最后两个元素
                    current_module['variables'][current_var]['width'] = msb - lsb + 1
                    current_module['variables'][current_var]['msb'] = msb
                    current_module['variables'][current_var]['lsb'] = lsb

    # 修改输出格式以支持多模块
    with open('variables.txt', 'w', encoding='utf-8') as txtfile:
        #txtfile.write("变量名\t所属端口\t变量类型\t位宽\n")
        for module in modules.values():  # Changed from modules -> modules.values()
            txtfile.write(f"\nModuleName: {module['name']}\n")
            for name, info in module['variables'].items():
                var_type = info['var_type'] or 'Wire'
                line = f"{name}\t{info['port']}\t{var_type}\t\n"
                txtfile.write(line)

    # Add return statement at the very end
    return modules  # <-- This was missing

# 修改classify_variables函数
def classify_variables(variables_data, output_dir='.'):
    """添加输出目录支持"""
    # 创建分类存储结构
    input_data = defaultdict(list)
    output_data = defaultdict(list)
    wires_data = defaultdict(list)  # 新增wire存储
    regs_data = defaultdict(list)    # 新增reg存储
    
    # 添加空值检查
    if not variables_data or 'modules' not in variables_data:
        raise ValueError("Invalid variables_data structure")
        
    # 修改遍历方式（直接通过模块名匹配）
    for mod_name, module in variables_data.get('modules', {}).items():
        variables = module.get('variables', {})
        for var_name, var_info in variables.items():
            # 直接从variables_data获取位宽信息
            msb = var_info.get('msb', 0)
            lsb = var_info.get('lsb', 0)
            width = var_info.get('width', 1)
            # 处理单比特信号显示
            bw = '1' if width == 1 else f'[{msb}:{lsb}]'

            # 构建记录（添加类型字段）
            record = {
                'name': var_name,
                'type': var_info.get('var_type', 'Wire').lower(),  # 统一转为小写
                'width': bw,
                'port': var_info.get('port', 'internal')
            }
            
            # 分类存储（修改过滤条件）
            port_type = var_info.get('port', '').lower()
            
            # 仅保留output和internal类型
            if record['port'] in ('output', 'internal'):
                if record['type'] == 'wire':
                    wires_data[mod_name].append(record)
                elif record['type'] == 'reg':
                    regs_data[mod_name].append(record)
            if port_type == 'input':
                input_data[mod_name].append(record)
            elif port_type == 'output':
                output_data[mod_name].append(record)

    # 修改后的文件写入逻辑
    def write_files(filename, data):
        with open(os.path.join(output_dir, filename), 'a') as f:
            for mod, vars in data.items():
                # 新增排序逻辑：input -> output -> internal
                sorted_vars = sorted(vars, key=lambda x: (
                    0 if x['port'] == 'input' else 
                    1 if x['port'] == 'output' else 2, 
                    x['name']))
                
                for var in sorted_vars:
                    f.write(f"{mod} {var['name']} {var['width']} {var['port']}\n")

    # 写入新增文件
    write_files('wires.txt', wires_data)
    write_files('regs.txt', regs_data)
    
    # 更新原有文件格式（添加类型字段）
    with open(os.path.join(output_dir, 'input.txt'), 'a') as f:
        for mod, vars in input_data.items():
            for var in vars:
                f.write(f"{var['name']} {var['width']} {mod} {var['type']}\n")
    
    with open(os.path.join(output_dir, 'output.txt'), 'a') as f:
        for mod, vars in output_data.items():
            for var in vars:
                f.write(f"{var['name']} {var['width']} {mod} {var['type']}\n")


##################################################################
#
#   描述：从AST语法树中提取信号的位宽信息
#
##################################################################
def parse_bitwidth_from_ast(filepath):
    module_pattern = re.compile(r'ModuleDef: (\w+)')
    decl_pattern = re.compile(r'(Input|Output|Wire|Reg): (\w+),')
    width_pattern = re.compile(r'IntConst: (\d+)')
    
    bitwidth_data = {}
    current_module = None
    current_var = None
    width_values = []
    
    with open(filepath, 'r') as f:
        for line in f:
            # 匹配模块定义
            module_match = module_pattern.search(line)
            if module_match:
                current_module = module_match.group(1)
                bitwidth_data[current_module] = {}
                continue
                
            # 匹配变量声明
            decl_match = decl_pattern.search(line)
            if decl_match and current_module:
                _, var_name = decl_match.groups()
                if var_name not in bitwidth_data[current_module]:
                    bitwidth_data[current_module][var_name] = {
                        'msb': 0,
                        'lsb': 0,
                        'width': 1
                    }
                current_var = var_name
                width_values = []
                continue
                
            # 收集位宽数值
            width_match = width_pattern.search(line)
            if width_match and current_var:
                width_values.append(int(width_match.group(1)))
                if len(width_values) == 2:
                    # 按Verilog标准，第一个是msb，第二个是lsb
                    msb, lsb = width_values
                    bitwidth_data[current_module][current_var]['msb'] = msb
                    bitwidth_data[current_module][current_var]['lsb'] = lsb
                    bitwidth_data[current_module][current_var]['width'] = msb - lsb + 1
                    width_values = []
    
    return bitwidth_data


##################################################################
#
#   描述：提取dut的信号
#   功能：
#   1、对dut生成ast语法树
#   2、根据ast语法树，提取input、output、wire和reg信号列表
#   3、将提取到的信号列表，按照指定类型输出到文件内
#
#################################################################
def extract_dut_signal(filepath, output_dir='.'):
    parse_verilog(filepath)             # 解析AST语法树
    ast_output_path = os.path.join(output_dir, 'ast_output.txt')
    if os.path.exists(ast_output_path):
        os.remove(ast_output_path)
    os.replace('ast_output.txt', ast_output_path)
    
    modules_dict = parse_ast_output(ast_output_path)            # 提取信号列表
    
    bitwidth_data = parse_bitwidth_from_ast(ast_output_path)    # 修正位宽信息
    for mod_name, variables in bitwidth_data.items():
        if mod_name in modules_dict:
            for var_name, bw_info in variables.items():
                if var_name in modules_dict[mod_name]['variables']:
                    modules_dict[mod_name]['variables'][var_name].update(bw_info)

    # 新增变量类型修正逻辑
    for mod in modules_dict.values():
        for var_info in mod['variables'].values():
            if var_info['var_type'] is None:
                var_info['var_type'] = 'wire'

    # 生成最终文件到指定目录
    variables_data = {'modules': modules_dict}
    classify_variables(variables_data, output_dir)
    
    # 移动variables.txt到输出目录
    variables_txt = os.path.join(output_dir, 'variables.txt')
    if os.path.exists(variables_txt):    # 新增存在性检查
        os.remove(variables_txt)         # 强制删除已存在文件
    os.replace('variables.txt', variables_txt)  # 改为使用替换操作
    os.remove('parser.out')
    os.remove('parsetab.py')
    
    # 控制输出文件数量
    os.remove(output_dir + '/ast_output.txt')
    os.remove(output_dir + '/variables.txt')
    #os.remove(output_dir + '/regs.txt')
    #os.remove(output_dir + '/wires.txt')
    os.remove(output_dir + '/input.txt')
    #os.remove(output_dir + '/output.txt')

# 修改main函数测试
if __name__ == '__main__':
    # 示例：输出到output目录
    # extract_dut_signal("D://test//s27c.v", output_dir="D://test//output")
    parse_verilog("D:\\哈工大博士\\毕业论文\\benchmark\\ISCAS'89\\s27.v")
    