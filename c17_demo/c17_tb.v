
`timescale 1ns / 1ps

module c17_tb ();

    reg [4:0] in;
    reg clk;

    wire [1:0] fl_out;
    wire [1:0] gd_out;

    reg [1:0] o_fl_out;     // 这个信号用于模拟时序屏蔽效应
    reg [1:0] o_gd_out;     // 这个信号用于模拟时序屏蔽效应

    integer i;

    // 模块例化，例化两个模块，分别是待注入的模块和黄金模块
    c17 c17_fl(
        // input signal
        .N1(in[0]),
        .N2(in[1]),
        .N3(in[2]),
        .N6(in[3]),
        .N7(in[4]),
        // output signal
        .N22(fl_out[0]),
        .N23(fl_out[1])
    );

    c17 c17_gd(
        // input signal
        .N1(in[0]),
        .N2(in[1]),
        .N3(in[2]),
        .N6(in[3]),
        .N7(in[4]),
        // output signal
        .N22(gd_out[0]),
        .N23(gd_out[1])
    );

    initial begin
        clk = 0;
        in = 5'b00000;
        o_fl_out = 2'b00;
        o_gd_out = 2'b00;
        cnt = 32'd0;
        forever #5 clk = ~clk; // 10ns = 100MHz
    end

    initial begin
        for (i = 0; i<10000; i=i+1) begin       // 这里的10000是故障注入次数，要执行多少次故障注入，这里就要模拟多少次。
            in = $random;
            #10;
        end
        $finish;
    end

    always @(posedge clk) begin                 // 这里模拟时序屏蔽效应
        o_fl_out = fl_out;
        o_gd_out = gd_out;
    end

    always @(negedge clk) begin                 // 信号复位
        o_fl_out = 2'b00;
        o_gd_out = 2'b00;
    end


endmodule