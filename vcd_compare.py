from vcdvcd import VCDVCD
import os

class VCDComparator:
    def __init__(self):
        self.vcd_gd = None
        self.vcd_fl = None
        self.signals_gd = self._get_all_signal_names(self.vcd_gd)
        self.signals_fl = self._get_all_signal_names(self.vcd_fl)
        self.data_gd = self._get_all_signal_waves(self.vcd_gd)
        self.data_fl = self._get_all_signal_waves(self.vcd_fl)
    
    def _get_all_signal_names(self, vcd: VCDVCD):
        return vcd.get_signals()
    
    def _get_all_signal_waves(self, vcd: VCDVCD):
        return vcd.get_data()
    
    def compare_signals_number(self):
        if len(self.signals_gd) != len(self.signals_gd):
            print("Error: Number of signals in the two files do not match.")
            return False
        return True
    
    def compare_wave(self, start_time, end_time):
        # 比较每个信号的值变化
        for signal_gd, signal_fl in zip(self.signals_gd, self.signals_fl):
            # 检查信号名称是否相同
            if signal_gd != signal_fl:
                print(f"Error: Signal names do not match: {signal_gd} vs {signal_fl}")
                return False

            # 获取信号的值变化
            flag_gd = self.vcd_gd.references_to_ids[signal_gd]
            flag_fl = self.vcd_fl.references_to_ids[signal_fl]
            tv_gd = self.data_gd[flag_gd].tv
            tv_fl = self.data_fl[flag_fl].tv

            # 缩减波形
            tv_new_gd = self.adjust_tv_list(tv_gd, start_time, end_time)
            tv_new_fl = self.adjust_tv_list(tv_fl, start_time, end_time)

            # 比对波形
            if tv_new_gd != tv_new_fl:
                # print(f"Error: Number of changes for signal {signal_gd} do not match.")
                return False

        return True
    
    def adjust_tv_list(self, tv, start, end):
        """
        根据 start 和 end 调整 tv 列表
        
        参数:
            tv: 原始列表，格式如 [(时间1, 值1), (时间2, 值2), ...]
            start: 起始时间
            end: 结束时间
            
        返回:
            调整后的新列表
        """
        if not tv:
            return []
        
        # 创建新列表的副本
        new_tv = tv.copy()
        
        # 处理起始点
        for i in range(len(new_tv)-1):
            t1, v1 = new_tv[i]
            t2, v2 = new_tv[i+1]
            if t1 <= start < t2:
                # 替换前一个点
                new_tv[i] = (start, v1)
                # 移除 start 之前的所有点
                new_tv = [(t, v) for t, v in new_tv if t >= start]
                break
            if start == t2:
                # 移除 start 之前的所有点
                new_tv = [(t, v) for t, v in new_tv if t >= start]
                break
        
        # 如果 start 大于所有时间点，取最后一个值并构造 (start, v_last)
        if len(new_tv) > 0 and start > new_tv[-1][0]:
            last_t, last_v = new_tv[-1]
            new_tv = [(start, last_v)]  # 使用最后一个值
        
        # 处理结束点
        for i in range(len(new_tv)-1):
            t1, v1 = new_tv[i]
            t2, v2 = new_tv[i+1]
            if t1 <= end < t2:
                # 移除 end 之后的所有点
                new_tv = [(t, v) for t, v in new_tv if t <= end]
                break
        
        return new_tv

# 示例使用
if __name__ == "__main__":
    file2 = "fl_wave_0.vcd"
    file1 = "gd_wave_0.vcd"
    comparator = VCDComparator(file1, file2)
    # compare_vcd_files(file1, file2, 5, 15)
    comparator.compare_signals_number()
    comparator.compare_wave(5, 15)