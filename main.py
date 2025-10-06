import para_gener as pg
import simulate as smu
import result_analysis as ra
from fi_class import dut, injector
import argparse


def monte_carlo_fi(proj_dir, top_module, tb_name, fi_num, period, sim_time, pulse_width, circuit_type, dff_num):
    dut.proj_dir    = proj_dir
    dut.top_module  = top_module
    dut.tb_name     = tb_name
    dut.observe_signal = dut.top_module + "/o*"
    dut.circuit_type = circuit_type

    injector.fi_num      = fi_num
    injector.period      = period
    injector.pulse_width = pulse_width
    injector.dff_num     = dff_num
    injector.sim_time    = sim_time

    # 主程序控制逻辑
    smu.mc_fault_injection_simulation()
    if circuit_type == "com":
        ra.compare_vcd_files("MC")
    else:
        ra.compare_seq_vcd_files("MC")

def importance_sample_monte_carlo_fi(proj_dir, top_module, tb_name, fi_num, period, sim_time, pulse_width, circuit_type, dff_num):
    dut.proj_dir    = proj_dir
    dut.top_module  = top_module
    dut.tb_name     = tb_name
    dut.observe_signal = dut.top_module + "/o*"
    dut.circuit_type = circuit_type

    injector.fi_num      = fi_num
    injector.period      = period
    injector.pulse_width = pulse_width
    injector.dff_num     = dff_num
    injector.sim_time    = sim_time

    # 主程序控制逻辑
    smu.ismc_fault_injection_simulation()
    if circuit_type == "com":
        ra.compare_vcd_files("ISMC")
    else:
        ra.compare_seq_vcd_files("ISMC")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--proj_dir', type=str, required=True, help="dut project directory")
    parser.add_argument('--top_module', type=str, required=True, help="testbench module name")
    parser.add_argument('--tb_name', type=str, required=True, help="testbench file name")
    parser.add_argument('--fi_num', type=int, default=100000, help="fault inject number")
    parser.add_argument('--clk_period', type=int, default=10, help="circuit clock period(ns)")
    parser.add_argument('--sim_time', type=int, default=10, help="circuit simulation period(ns)")
    parser.add_argument('--pulse_width', type=int, default=200, help="transient pulse width(ps)")
    parser.add_argument('--circuit_type', type=str, required=True, help="circuit type: com, seq")
    parser.add_argument('--fi_mode', type=str, required=True, help="fault injection mode: MC, ISMC")
    parser.add_argument('--dff_num', type=int, default=0, help="dff number")
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    # python3 .\main.py --proj_dir D://doctor_data//paper_data//conference_paper_data//test// --top_module c17_tb --tb_name c17_tb_template.v --fi_type SET --pulse_width 200 --period 10 --fi_num 10
    # python3 .\main.py --proj_dir D://doctor_data//paper_data//monte_carlo//c1355//andnot// --top_module c1355_tb --tb_name c1355_tb.v --fi_num 1000 --clk_period 10 --sim_time 10 --pulse_width 100 --circuit_type com --fi_mode ISMC

    if args.fi_mode == "MC":
        monte_carlo_fi(args.proj_dir, args.top_module, args.tb_name, args.fi_num, args.clk_period, args.sim_time, args.pulse_width, args.circuit_type, args.dff_num)
    elif args.fi_mode == "ISMC":
        importance_sample_monte_carlo_fi(args.proj_dir, args.top_module, args.tb_name, args.fi_num, args.clk_period, args.sim_time, args.pulse_width, args.circuit_type, args.dff_num)
    else:
        print(f"no support this mode: {args.fi_mode}")