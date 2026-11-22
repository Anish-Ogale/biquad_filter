v {xschem version=3.4.5 file_version=1.2
* SPDX-License-Identifier: Apache-2.0
*
* Fully differential two-stage Miller op-amp, Sky130 5 V devices. v3
* Netlist-equivalent to design/opamp/opamp_2stage.spice (Cc=5p Rz=550 via .param
* in the testbench).  Devices:
*   M0 (pfet W20 m2): tail current source, G=pbias, S=vdd, D=sp
*   M1/M2 (pfet W20): PMOS input pair, common source sp
*   M3/M4 (nfet W5): NMOS mirror load (diode a -> b)
*   M5p/M5n (nfet W20): NMOS common-source second stage
*   M6p/M6n (pfet W20 m2): PMOS loads, gate = cmfb (ideal CMFB)
*   Cc=5p + Rz=550 nulling on each side; ideal algebraic CMFB (Bcmfb).
* Devices are label-stub wired: each pin has an explicit named connector;
* net identity = label name.
}
G {}
K {type=subcircuit
format="@name @pinlist"
template="name=opamp_2stage"}
V {}
S {}
E {}

N 320 -170 350 -170 {}
N 250 -200 280 -200 {}
N 320 -230 350 -230 {}
N 320 -200 365 -200 {}
N 320 -410 350 -410 {}
N 250 -440 280 -440 {}
N 320 -470 350 -470 {}
N 320 -440 365 -440 {}
N 320 -650 350 -650 {}
N 250 -680 280 -680 {}
N 320 -710 350 -710 {}
N 320 -680 365 -680 {}
N 320 -950 350 -950 {}
N 250 -920 280 -920 {}
N 320 -890 350 -890 {}
N 320 -920 365 -920 {}
N 320 -1190 350 -1190 {}
N 250 -1160 280 -1160 {}
N 320 -1130 350 -1130 {}
N 320 -1160 365 -1160 {}
N 320 -1430 350 -1430 {}
N 250 -1400 280 -1400 {}
N 320 -1370 350 -1370 {}
N 320 -1400 365 -1400 {}
N 320 -1670 350 -1670 {}
N 250 -1640 280 -1640 {}
N 320 -1610 350 -1610 {}
N 320 -1640 365 -1640 {}
N 320 -1850 350 -1850 {}
N 250 -1880 280 -1880 {}
N 320 -1910 350 -1910 {}
N 320 -1880 365 -1880 {}
N 320 -2090 350 -2090 {}
N 250 -2120 280 -2120 {}
N 320 -2150 350 -2150 {}
N 320 -2120 365 -2120 {}
N 900 -280 900 -230 {}
N 900 -170 900 -120 {}
N 900 -520 900 -470 {}
N 900 -410 900 -360 {}
N 900 -760 900 -710 {}
N 900 -650 900 -600 {}
N 900 -1000 900 -950 {}
N 900 -890 900 -840 {}
N 1200 -1240 1200 -1190 {}
N 1200 -1130 1200 -1080 {}
N 1200 -1480 1200 -1430 {}
N 1200 -1370 1200 -1320 {}
N 1200 -1720 1200 -1670 {}
N 1200 -1610 1200 -1560 {}
N 1600 600 1640 600 {}
N 1600 540 1640 540 {}
N 1600 480 1640 480 {}
N 1600 420 1640 420 {}
N 1600 360 1640 360 {}
N 1600 300 1640 300 {}
N 1600 240 1640 240 {}

C {sky130_fd_pr/pfet_g5v0d10v5.sym} 300 -200 0 0 {name=M0
L=0.5
W=20
nf=1 mult=2
model=pfet_g5v0d10v5
spiceprefix=X
}
C {devices/lab_pin.sym} 350 -170 0 0 {name=lp_M0_D
lab=sp
}
C {devices/lab_pin.sym} 250 -200 0 0 {name=lp_M0_G
lab=pbias
}
C {devices/lab_pin.sym} 350 -230 0 0 {name=lp_M0_S
lab=vdd
}
C {devices/lab_pin.sym} 365 -200 0 0 {name=lp_M0_B
lab=vdd
}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 300 -440 0 0 {name=M1
L=0.5
W=20
nf=1 mult=1
model=pfet_g5v0d10v5
spiceprefix=X
}
C {devices/lab_pin.sym} 350 -410 0 0 {name=lp_M1_D
lab=a
}
C {devices/lab_pin.sym} 250 -440 0 0 {name=lp_M1_G
lab=inp
}
C {devices/lab_pin.sym} 350 -470 0 0 {name=lp_M1_S
lab=sp
}
C {devices/lab_pin.sym} 365 -440 0 0 {name=lp_M1_B
lab=vdd
}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 300 -680 0 0 {name=M2
L=0.5
W=20
nf=1 mult=1
model=pfet_g5v0d10v5
spiceprefix=X
}
C {devices/lab_pin.sym} 350 -650 0 0 {name=lp_M2_D
lab=b
}
C {devices/lab_pin.sym} 250 -680 0 0 {name=lp_M2_G
lab=inn
}
C {devices/lab_pin.sym} 350 -710 0 0 {name=lp_M2_S
lab=sp
}
C {devices/lab_pin.sym} 365 -680 0 0 {name=lp_M2_B
lab=vdd
}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 300 -920 0 0 {name=M3
L=0.5
W=5
nf=1 mult=1
model=nfet_g5v0d10v5
spiceprefix=X
}
C {devices/lab_pin.sym} 350 -950 0 0 {name=lp_M3_D
lab=a
}
C {devices/lab_pin.sym} 250 -920 0 0 {name=lp_M3_G
lab=a
}
C {devices/lab_pin.sym} 350 -890 0 0 {name=lp_M3_S
lab=0
}
C {devices/lab_pin.sym} 365 -920 0 0 {name=lp_M3_B
lab=0
}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 300 -1160 0 0 {name=M4
L=0.5
W=5
nf=1 mult=1
model=nfet_g5v0d10v5
spiceprefix=X
}
C {devices/lab_pin.sym} 350 -1190 0 0 {name=lp_M4_D
lab=b
}
C {devices/lab_pin.sym} 250 -1160 0 0 {name=lp_M4_G
lab=a
}
C {devices/lab_pin.sym} 350 -1130 0 0 {name=lp_M4_S
lab=0
}
C {devices/lab_pin.sym} 365 -1160 0 0 {name=lp_M4_B
lab=0
}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 300 -1400 0 0 {name=M5p
L=0.5
W=20
nf=1 mult=1
model=nfet_g5v0d10v5
spiceprefix=X
}
C {devices/lab_pin.sym} 350 -1430 0 0 {name=lp_M5p_D
lab=outp
}
C {devices/lab_pin.sym} 250 -1400 0 0 {name=lp_M5p_G
lab=a
}
C {devices/lab_pin.sym} 350 -1370 0 0 {name=lp_M5p_S
lab=0
}
C {devices/lab_pin.sym} 365 -1400 0 0 {name=lp_M5p_B
lab=0
}
C {sky130_fd_pr/nfet_g5v0d10v5.sym} 300 -1640 0 0 {name=M5n
L=0.5
W=20
nf=1 mult=1
model=nfet_g5v0d10v5
spiceprefix=X
}
C {devices/lab_pin.sym} 350 -1670 0 0 {name=lp_M5n_D
lab=outn
}
C {devices/lab_pin.sym} 250 -1640 0 0 {name=lp_M5n_G
lab=b
}
C {devices/lab_pin.sym} 350 -1610 0 0 {name=lp_M5n_S
lab=0
}
C {devices/lab_pin.sym} 365 -1640 0 0 {name=lp_M5n_B
lab=0
}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 300 -1880 0 0 {name=M6p
L=0.5
W=20
nf=1 mult=2
model=pfet_g5v0d10v5
spiceprefix=X
}
C {devices/lab_pin.sym} 350 -1850 0 0 {name=lp_M6p_D
lab=vdd
}
C {devices/lab_pin.sym} 250 -1880 0 0 {name=lp_M6p_G
lab=cmfb
}
C {devices/lab_pin.sym} 350 -1910 0 0 {name=lp_M6p_S
lab=outp
}
C {devices/lab_pin.sym} 365 -1880 0 0 {name=lp_M6p_B
lab=vdd
}
C {sky130_fd_pr/pfet_g5v0d10v5.sym} 300 -2120 0 0 {name=M6n
L=0.5
W=20
nf=1 mult=2
model=pfet_g5v0d10v5
spiceprefix=X
}
C {devices/lab_pin.sym} 350 -2090 0 0 {name=lp_M6n_D
lab=vdd
}
C {devices/lab_pin.sym} 250 -2120 0 0 {name=lp_M6n_G
lab=cmfb
}
C {devices/lab_pin.sym} 350 -2150 0 0 {name=lp_M6n_S
lab=outn
}
C {devices/lab_pin.sym} 365 -2120 0 0 {name=lp_M6n_B
lab=vdd
}
C {devices/capa.sym} 900 -200 0 0 {name=Cc1
value=5p
}
C {devices/lab_pin.sym} 900 -280 0 0 {name=lp_Cc1_p
lab=a
}
C {devices/lab_pin.sym} 900 -120 0 0 {name=lp_Cc1_m
lab=mid1
}
C {devices/res.sym} 900 -440 0 0 {name=Rz1
value=550
}
C {devices/lab_pin.sym} 900 -520 0 0 {name=lp_Rz1_P
lab=mid1
}
C {devices/lab_pin.sym} 900 -360 0 0 {name=lp_Rz1_M
lab=outp
}
C {devices/capa.sym} 900 -680 0 0 {name=Cc2
value=5p
}
C {devices/lab_pin.sym} 900 -760 0 0 {name=lp_Cc2_p
lab=b
}
C {devices/lab_pin.sym} 900 -600 0 0 {name=lp_Cc2_m
lab=mid2
}
C {devices/res.sym} 900 -920 0 0 {name=Rz2
value=550
}
C {devices/lab_pin.sym} 900 -1000 0 0 {name=lp_Rz2_P
lab=mid2
}
C {devices/lab_pin.sym} 900 -840 0 0 {name=lp_Rz2_M
lab=outn
}
C {devices/vsource.sym} 1200 -1160 0 0 {name=Vcmref
value=1.65
}
C {devices/lab_pin.sym} 1200 -1240 0 0 {name=lp_Vcmref_p
lab=vcmref
}
C {devices/lab_pin.sym} 1200 -1080 0 0 {name=lp_Vcmref_m
lab=0
}
C {devices/bsource.sym} 1200 -1400 0 0 {name=Bavg
VAR=V FUNC="'0.5*(v(outp)+v(outn))'"
}
C {devices/lab_pin.sym} 1200 -1480 0 0 {name=lp_Bavg_p
lab=vcm_s
}
C {devices/lab_pin.sym} 1200 -1320 0 0 {name=lp_Bavg_m
lab=0
}
C {devices/bsource.sym} 1200 -1640 0 0 {name=Bcmfb
VAR=V FUNC="'1.65 + tanh(0.2 + 20*(v(vcm_s) - v(vcmref)))'"
}
C {devices/lab_pin.sym} 1200 -1720 0 0 {name=lp_Bcmfb_p
lab=cmfb
}
C {devices/lab_pin.sym} 1200 -1560 0 0 {name=lp_Bcmfb_m
lab=0
}
C {devices/ipin.sym} 1600 600 0 0 {name=pp_inp
lab=inp
}
C {devices/ipin.sym} 1600 540 0 0 {name=pp_inn
lab=inn
}
C {devices/opin.sym} 1600 480 0 0 {name=pp_outp
lab=outp
}
C {devices/opin.sym} 1600 420 0 0 {name=pp_outn
lab=outn
}
C {devices/iopin.sym} 1600 360 0 0 {name=pp_vdd
lab=vdd
}
C {devices/iopin.sym} 1600 300 0 0 {name=pp_vss
lab=vss
}
C {devices/ipin.sym} 1600 240 0 0 {name=pp_pbias
lab=pbias
}
