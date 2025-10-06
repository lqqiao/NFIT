# NFIT
A netlist-level fault injection tool is designed to support SET fault model.

# 故障注入工具使用方法
## 环境依赖
modelsim仿真器
python包：vcdvcd、pyverilog

## 数据准备
|- 任意文件夹
|   |- dut
|   |   |- c17.v
|   |- c17_tb.v

ps: testbench规范见c17和s27的示例

1) perfect_fi_signal.txt生成
1.1 命令
'''bash
python3 ./para_gener.py --proj_dir /path/to/circuit
'''

示例：python3 ./para_gener.py --proj_dir ~/c17
之后会在c17目录下，生成perfect_fi_signal.txt，此时电路的文件夹组成

|- 任意文件夹
|   |- dut
|   |   |- c17.v
|   |- c17_tb.v
|   |- perfect_fi_signal.txt
|   |- tmp/                 # 中间文件，无需关注

1.2 双击打开perfect_fi_signal.txt，完成路径替换
示例：在c17电路的perfect_fi_signal.txt，搜索c17，然后将c17全部替换成c17_tb/c17_fl

## 基于蒙卡的组合逻辑电路故障注入使用方法
故障注入命令：
python3 .\main.py --proj_dir /path/to/circuit --top_module <tb_top_module_name> --tb_name <tb_name> --fi_num <fault_injection_number> --clk_period <clock_period_ns> --sim_time <single_simulation_time_ns> --pulse_width <SET's_width_ps> --circuit_type com --fi_mode MC

示例：python3 .\main.py --proj_dir ~/c17 --top_module c17_tb --tb_name c17_tb.v --fi_num 10000 --clk_period 10 --sim_time 10 --pulse_width 200 --circuit_type com --fi_mode MC

此时，电路的文件夹组成
|- 任意文件夹
|   |- dut/
|   |   |- c17.v
|   |- c17_tb.v
|   |- perfect_fi_signal.txt
|   |- tmp/                 # 中间文件，无需关注
|   |- fault_data/
|   |   |- scripts/      
|   |   |   |- mc_com_fault_injector.tcl    # 故障注入的执行脚本
|   |   |- fault_wave/
|   |   |   |- fl_wave.vcd                  # 仿真的vcd波形文件
|   |- work/                # modelsim产生的临时工作目录
|   |- output_signal_result.txt     # 输出信号的失效率
|   |- signal_result.txt            # 逻辑门的失效率
|   |- signal_record.txt            # 故障注入每次注入的信号

## 基于重要性采样的组合逻辑电路故障注入使用方法
故障注入命令：
python3 .\main.py --proj_dir /path/to/circuit --top_module <tb_top_module_name> --tb_name <tb_name> --fi_num <fault_injection_number> --clk_period <clock_period_ns> --sim_time <single_simulation_time_ns> --pulse_width <SET's_width_ps> --circuit_type com --fi_mode ISMC

示例：python3 .\main.py --proj_dir ~/c17 --top_module c17_tb --tb_name c17_tb.v --fi_num 10000 --clk_period 10 --sim_time 10 --pulse_width 200 --circuit_type com --fi_mode ISMC

文件夹的组成同上。

## 基于蒙卡的时序逻辑电路故障注入使用方法
故障注入命令：
python3 .\main.py --proj_dir /path/to/circuit --top_module <tb_top_module_name> --tb_name <tb_name> --fi_num <fault_injection_number> --clk_period <clock_period_ns> --sim_time <single_simulation_time_ns> --pulse_width <SET's_width_ps> --circuit_type seq --fi_mode MC --dff_num <dff_number_of_circuit>

示例：python3 .\main.py --proj_dir ~/s27 --top_module s27_tb --tb_name s27_tb.v --fi_num 10000 --clk_period 10 --sim_time 80 --pulse_width 200 --circuit_type seq --fi_mode MC --dff_num 3

## 基于重要性采样的时序逻辑电路故障注入使用方法
故障注入命令：
python3 .\main.py --proj_dir /path/to/circuit --top_module <tb_top_module_name> --tb_name <tb_name> --fi_num <fault_injection_number> --clk_period <clock_period_ns> --sim_time <single_simulation_time_ns> --pulse_width <SET's_width_ps> --circuit_type seq --fi_mode ISMC --dff_num <dff_number_of_circuit>

示例：python3 .\main.py --proj_dir ~/s27 --top_module s27_tb --tb_name s27_tb.v --fi_num 10000 --clk_period 10 --sim_time 80 --pulse_width 200 --circuit_type seq --fi_mode ISMC --dff_num 3
