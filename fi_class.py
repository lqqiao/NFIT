class Design_Under_Test:
    def __init__(self):
        self.proj_dir = None
        self.top_module = None
        self.tb_name = None
        self.observe_signal = None
        self.circuit_type = None
    
    ## 生成黄金脚本
    def individual_gdn_srpt(self, gd_srpt_path, gd_wave_path):
        ## 完成文本内容的替换
        with open(gd_srpt_path, "r", encoding="utf-8") as file:
            text = file.read()
        # 替换规则
        replace_rules = {
            "[proj_dir]": self.proj_dir.replace("\\", "/"),
            "[top_module]": self.top_module,
            "[observe_signal]": self.observe_signal,
            "[gd_wv_path]": gd_wave_path.replace("\\", "/")
        }
        # 批量替换
        for old, new in replace_rules.items():
            text = text.replace(old, new)

        with open(gd_srpt_path, "w", encoding="utf-8") as file:
            file.write(text)


class Injector:
    def __init__(self):
        self.fi_num = None
        self.period = None
        self.pulse_width = None
        self.dff_num = None
        self.sim_time = None
    
    ## 生成注入脚本
    def generate_ismc_com_flt_srpt(self, proj_dir, top_module, observe_signal, fi_signal_filepath,
                            fl_srpt_path, fl_wv_path, fi_signal_record_filepath):
        ## 完成文本内容的替换
        with open(fl_srpt_path, "r", encoding="utf-8") as file:
            text = file.read()
        # 替换规则
        replace_rules = {
            "[proj_dir]": proj_dir.replace("\\", "/"),
            "[top_module]": top_module,
            "[observe_signal]": observe_signal,
            "[fi_signal_filepath]": str(fi_signal_filepath).replace("\\", "/"),
            "[fl_wv_path]": str(fl_wv_path).replace("\\", "/"),
            "[period]": str(self.period),
            "[pulse_width]": str(self.pulse_width),
            "[fi_signal_record_filepath]": str(fi_signal_record_filepath).replace("\\", "/"),
            "[fi_num]": str(self.fi_num)
        }

        # 批量替换
        for old, new in replace_rules.items():
            text = text.replace(old, new)

        with open(fl_srpt_path, "w", encoding="utf-8") as file:
            file.write(text)
    
    def generate_mc_com_flt_srpt(self, proj_dir, top_module, observe_signal, fi_signal_filepath,
                            fl_srpt_path, fl_wv_path, fi_signal_record_filepath):
        ## 完成文本内容的替换
        with open(fl_srpt_path, "r", encoding="utf-8") as file:
            text = file.read()
        # 替换规则
        replace_rules = {
            "[proj_dir]": proj_dir.replace("\\", "/"),
            "[top_module]": top_module,
            "[observe_signal]": observe_signal,
            "[fi_signal_filepath]": str(fi_signal_filepath).replace("\\", "/"),
            "[fl_wv_path]": str(fl_wv_path).replace("\\", "/"),
            "[period]": str(self.period),
            "[pulse_width]": str(self.pulse_width),
            "[fi_signal_record_filepath]": str(fi_signal_record_filepath).replace("\\", "/"),
            "[fi_num]": str(self.fi_num)
        }

        # 批量替换
        for old, new in replace_rules.items():
            text = text.replace(old, new)

        with open(fl_srpt_path, "w", encoding="utf-8") as file:
            file.write(text)
    
    def generate_seq_flt_srpt(self, proj_dir, top_module, observe_signal, fi_signal_filepath,
                            fl_srpt_path, fl_wv_path, fi_signal_record_filepath):
        ## 完成文本内容的替换
        with open(fl_srpt_path, "r", encoding="utf-8") as file:
            text = file.read()
        # 替换规则
        replace_rules = {
            "[proj_dir]": proj_dir.replace("\\", "/"),
            "[top_module]": top_module,
            "[observe_signal]": observe_signal,
            "[fi_signal_filepath]": str(fi_signal_filepath).replace("\\", "/"),
            "[fl_wv_path]": str(fl_wv_path).replace("\\", "/"),
            "[period]": str(self.period),
            "[pulse_width]": str(self.pulse_width),
            "[fi_signal_record_filepath]": str(fi_signal_record_filepath).replace("\\", "/"),
            "[fi_num]": str(self.fi_num),
            "[dff_num]": str(self.dff_num)
        }

        # 批量替换
        for old, new in replace_rules.items():
            text = text.replace(old, new)

        with open(fl_srpt_path, "w", encoding="utf-8") as file:
            file.write(text)

dut = Design_Under_Test()
injector = Injector()
