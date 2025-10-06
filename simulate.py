import os
import subprocess
import shutil
from fi_class import dut, injector

def generate_fault_waveform(fi_mode):
    signal_path = os.path.join(dut.proj_dir, "perfect_fi_signal.txt")
    signal_output_path = os.path.join(dut.proj_dir, "signal_record.txt")
    if os.path.exists(signal_output_path):
        os.remove(signal_output_path)

    fl_srpt_dir = os.path.join(dut.proj_dir, "fault_data", "scripts")
    fl_wave_dir = os.path.join(dut.proj_dir, "fault_data", "fault_wave")
    if os.path.exists(fl_srpt_dir):
        shutil.rmtree(fl_srpt_dir)
    os.makedirs(fl_srpt_dir, exist_ok=True)
    if os.path.exists(fl_wave_dir):
        shutil.rmtree(fl_wave_dir)
    os.makedirs(fl_wave_dir, exist_ok=True)
    
    if fi_mode == "MC":
        if dut.circuit_type == "com":
            fl_srpt_name = "mc_com_fault_injector.tcl"
            fl_srpt_path = os.path.join(fl_srpt_dir, fl_srpt_name)
            shutil.copy("./tcl/mc_com_fault_injector.tcl", fl_srpt_path)
            fl_wv_path = os.path.join(fl_wave_dir, "fl_wave.vcd")
                
            injector.generate_mc_com_flt_srpt(dut.proj_dir, dut.top_module, dut.observe_signal, signal_path,
                                        fl_srpt_path, fl_wv_path, signal_output_path)
        elif dut.circuit_type == "seq":
            fl_srpt_name = "mc_seq_fault_injector.tcl"
            fl_srpt_path = os.path.join(fl_srpt_dir, fl_srpt_name)
            shutil.copy("./tcl/mc_seq_fault_injector.tcl", fl_srpt_path)
            fl_wv_path = os.path.join(fl_wave_dir, "fl_wave.vcd")
                
            injector.generate_seq_flt_srpt(dut.proj_dir, dut.top_module, dut.observe_signal, signal_path,
                                        fl_srpt_path, fl_wv_path, signal_output_path)
        else:
            print(f"no support this circuit type: {dut.circuit_type}")
    elif fi_mode == "ISMC":
        if dut.circuit_type == "com":
            fl_srpt_name = "ismc_com_fault_injector.tcl"
            fl_srpt_path = os.path.join(fl_srpt_dir, fl_srpt_name)
            shutil.copy("./tcl/ismc_com_fault_injector.tcl", fl_srpt_path)
            fl_wv_path = os.path.join(fl_wave_dir, "fl_wave.vcd")
                
            injector.generate_ismc_com_flt_srpt(dut.proj_dir, dut.top_module, dut.observe_signal, signal_path,
                                        fl_srpt_path, fl_wv_path, signal_output_path)
        elif dut.circuit_type == "seq":
            fl_srpt_name = "ismc_seq_fault_injector.tcl"
            fl_srpt_path = os.path.join(fl_srpt_dir, fl_srpt_name)
            shutil.copy("./tcl/ismc_seq_fault_injector.tcl", fl_srpt_path)
            fl_wv_path = os.path.join(fl_wave_dir, "fl_wave.vcd")
                
            injector.generate_seq_flt_srpt(dut.proj_dir, dut.top_module, dut.observe_signal, signal_path,
                                        fl_srpt_path, fl_wv_path, signal_output_path)
        else:
            print(f"no support this circuit type: {dut.circuit_type}")
    else:
        print(f"no support this mode: {fi_mode}")


    
    current_dir = os.getcwd()
    os.chdir(dut.proj_dir)
    subprocess.run(["vsim", "-batch", "-do", fl_srpt_path.replace("\\", "/")])
    os.chdir(current_dir)
    # os.remove("./modelsim.ini")
    
def generate_seq_fault_waveform():
    signal_path = os.path.join(dut.proj_dir, "perfect_fi_signal.txt")
    signal_output_path = os.path.join(dut.proj_dir, "signal_record.txt")

#############################################################
#
#   具体功能：
#   1、生成所有需要的执行脚本，包括黄金脚本和注入脚本
#   2、运行所有的脚本，包括黄金脚本和注入脚本
#
##############################################################
def ismc_fault_injection_simulation():
    generate_fault_waveform("ISMC")


def mc_fault_injection_simulation():
    generate_fault_waveform("MC")


if __name__ == "__main__":
    print("test")
    fault_injection_simulation()