#########################################################################
##                        Modelsim TCL                                 ##
##             Created by HIT Microelectronics Center                  ##
#########################################################################

## 基础变量
set PROJ_DIR            [proj_dir]
set top_module          [top_module]
set observe_signal      [observe_signal]
set fi_signal_filepath  [fi_signal_filepath]
set fl_wv_path          [fl_wv_path]
set period              [period]
set pulse_width         [pulse_width]
set fi_signal_record_filepath   [fi_signal_record_filepath]
set fi_num              [fi_num]
set dff_num             [dff_num]


# 从文件中随机选择一行的过程
proc get_random_line {filename} {
    # 检查文件是否存在
    if {![file exists $filename]} {
        error "文件不存在: $filename"
    }
    
    # 检查文件是否可读
    if {![file readable $filename]} {
        error "文件不可读: $filename"
    }
    
    # 打开文件
    set fp [open $filename r]
    
    # 读取所有行到列表中
    set lines [split [read $fp] "\n"]
    
    # 关闭文件
    close $fp
    
    # 移除可能的空行
    set lines [lsearch -all -inline -not $lines ""]
    
    # 检查是否有有效行
    if {[llength $lines] == 0} {
        error "文件中没有有效行"
    }
    
    # 生成随机索引
    set random_index [expr {int(rand() * [llength $lines])}]
    
    # 返回随机行
    return [lindex $lines $random_index]
}

proc process_line {line} {
    set fields [regexp -all -inline {\S+} $line]  ;# 按空格分割为列表（忽略连续空格）
    
    if {[llength $fields] < 4} {
        error "Line does not contain at least 4 fields: '$line'"
    }
    
    set first [lindex $fields 0]
    # set second [lindex $fields 1]
    set fourth [lindex $fields 3]
    # set combined "$first"  ;# 直接拼接两个字段
    
    return [list $first $fourth]
}




############################ 清空软件残留信息 #############################
# # 退出之前仿真
# quit -sim
# # 清除命令和信息
# .main clear


############################# 编译和仿真文件 #########################
## 创建库
# 语法：vlib <library_name>
# 解释：使用该命令，ModelSim在当前目录下创建一个名为library_name的库文件夹
# 补充：库的作用——设计文件需要先编译到库中，然后才在仿真中被引用
vlib $PROJ_DIR/work

## 映射逻辑库到物理目录
vmap work $PROJ_DIR/work

## 编译源代码
# 语法：vlog <source_files>
# 解释：使用该命令，ModelSim会将名为source_files的源代码文件编译成相应的模型文件
# 编译修改后的文件，这里把设计文件和仿真文件分开放了，所以写两个
vlog -work $PROJ_DIR/work -sv "${PROJ_DIR}/dut/*.v" "${PROJ_DIR}/*.v"

## 启动仿真
# 语法：vsim <entity_name> -c
# 解释：使用该命令，ModelSim加载名为entity_name的顶层模块进行仿真。
#       -c  以命令行模式运行ModelSim
# -voptargs=+acc：不加这个参数看不到模块信号，add wave就会报错
# -wlf <wave_name>：保存波形文件
vsim -voptargs=+acc $top_module
vcd file ${fl_wv_path}


############################## 添加波形模板 #############################
## 只观察testbench中的输出信号
# add wave $observe_signal
vcd add $observe_signal

############################## 故障注入 #########################
for {set i 0} {$i < $fi_num} {incr i} {
    # 复位时刻 + 随机状态时刻
    set rst_time [expr {int(($dff_num + 1) * $period * 1000)}]
    run ${rst_time}ps

    # 随机选择注入信号
    if {[catch {set random_line [get_random_line $fi_signal_filepath]} error_msg]} {
        puts stderr "错误: $error_msg"
        exit 1
    }
    lassign [process_line $random_line] fi_signal signal_type
    echo "$i fi_signal: $fi_signal, type is $signal_type"
    set file_handle [open $fi_signal_record_filepath a]
    puts $file_handle "$fi_signal $signal_type"
    close $file_handle
    set signal_value [examine $fi_signal]

    # 检查注入信号的值
    if {$signal_value == "1'h1"} {
        set fault_value 0
    } elseif {$signal_value == "1'h0"} {
        set fault_value 1
    } else {
        echo "exception error"
    }

    # 注入时刻
    set inject_time [expr {int(rand() * ($period * 1000 + 1))}]
    set end_time [expr {$period * 1000 - $inject_time}]
    run ${inject_time}ps
    # 翻转信号
    if {$signal_type == "dff"} {
        if {$inject_time < ($period * 1000 / 2)} {
            set cancel_time [expr {int($period * 1000 / 2 - $inject_time)}]
            force $fi_signal $fault_value -cancel $cancel_time
        } elseif {$inject_time > ($period * 1000 / 2)}  {
            set cancel_time [expr {int($period * 1000 - $inject_time + $period * 1000 / 2)}]
            force $fi_signal $fault_value -cancel $cancel_time
        }
    } else {
        if {$end_time > $pulse_width} {
            force $fi_signal $fault_value -cancel $pulse_width
        } else {
            force $fi_signal $fault_value -cancel $end_time
        }
    }
    
    run ${end_time}ps
    set trans_time [expr {int($dff_num * $period * 1000)}]
    run ${trans_time}ps
}

run -all
