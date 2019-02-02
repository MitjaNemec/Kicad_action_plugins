EESchema Schematic File Version 4
LIBS:drawingcircuits-cache
EELAYER 26 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 3 5
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Sheet
S 5350 3650 550  300 
U 5BEB8BD4
F0 "SR_FLIP_FLOP_NAND2_2" 50
F1 "NAND2.sch" 50
F2 "A" I L 5350 3700 50 
F3 "B" I L 5350 3900 50 
F4 "Y" O R 5900 3800 50 
$EndSheet
Text Notes 5750 3850 2    50   ~ 0
NAND
$Sheet
S 5350 3100 550  300 
U 5BEB8BDF
F0 "SR_FLIP_FLOP_NAND2_1" 50
F1 "NAND2.sch" 50
F2 "A" I L 5350 3150 50 
F3 "B" I L 5350 3350 50 
F4 "Y" O R 5900 3250 50 
$EndSheet
Text Notes 5750 3300 2    50   ~ 0
NAND
Text HLabel 4950 3150 0    50   Input ~ 0
S
Text HLabel 4950 3700 0    50   Input ~ 0
R
Wire Wire Line
	5900 3250 6000 3250
Wire Wire Line
	5900 3800 6050 3800
Text HLabel 6300 3250 2    50   Output ~ 0
Q
Text HLabel 6300 3800 2    50   Output ~ 0
~Q
Wire Wire Line
	6000 3250 6000 3500
Connection ~ 6000 3250
Wire Wire Line
	6000 3250 6300 3250
Wire Wire Line
	5300 3550 6050 3550
Wire Wire Line
	6050 3550 6050 3800
Connection ~ 6050 3800
Wire Wire Line
	6050 3800 6300 3800
Wire Wire Line
	5350 3350 5300 3350
Wire Wire Line
	4950 3150 5350 3150
Wire Wire Line
	5350 3700 4950 3700
Wire Wire Line
	5300 3350 5300 3550
Wire Wire Line
	6000 3500 5250 3500
Wire Wire Line
	5250 3500 5250 3900
Wire Wire Line
	5250 3900 5350 3900
$EndSCHEMATC
