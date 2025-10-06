`timescale 1ns/1ps  // 设置时间单位/精度

module s27_tb;

    // 输入信号
    reg GND;    // 地
    reg VDD;    // 电源
    reg CK;     // 时钟
    reg RST;

    reg [3:0] in;
    integer i;
    integer j;
    
    // 输出信号
    wire fl_out;   // 输出
    wire gd_out;
    
    reg o_fl_out;
    reg o_gd_out;
    
    // 模块例化，例化两个模块，分别是待注入的模块和黄金模块
    s27 s27_fl (
        .GND(GND), 
        .VDD(VDD), 
        .CK(CK), 
        .RST(RST),
        .G0(in[0]), 
        .G1(in[1]), 
        .G2(in[2]), 
        .G3(in[3]), 
        .G17(fl_out)
    );

    s27 s27_gd (
        .GND(GND), 
        .VDD(VDD), 
        .CK(CK), 
        .RST(RST),
        .G0(in[0]), 
        .G1(in[1]), 
        .G2(in[2]), 
        .G3(in[3]), 
        .G17(gd_out)
    );
    
    // 时钟生成
    initial begin
        CK = 0;
        forever #5 CK = ~CK; // 10ns时钟周期(100MHz)
    end
    
    // 测试激励
    initial begin
        GND = 0;
        VDD = 1;
        
        for (i = 0; i<1000; i=i+1) begin        // 这里的10000是故障注入次数，要执行多少次故障注入，这里就要模拟多少次。
            RST = 1;  // 初始复位有效
            in = 4'b0000;
            
            // 复位阶段
            #10;      // 保持复位1个时钟周期
            
            // 释放复位
            RST = 0;

            // 设置电路的随机状态，这里的3是触发器的数量，有3个触发器，则最多需要3个时钟周期用于随机设置所有触发器的状态。
            // 第4个周期用于故障注入，再有3个时钟周期观察故障是否传播到电路的输出。
            // 算上前面的复位周期，因此，时序逻辑电路单次仿真需要2*n+2个周期
            for (j = 0; j < 2 * 3 + 1; j=j+1) begin
                in = $random;
                #10;
            end
        end
        $finish;
    end

    always @(posedge CK) begin
        o_fl_out = fl_out;
        o_gd_out = gd_out;
    end

    always @(negedge CK) begin
        o_fl_out = 0;
        o_gd_out = 0;
    end

endmodule