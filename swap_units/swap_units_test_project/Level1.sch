EESchema Schematic File Version 4
LIBS:swap_units_test-cache
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 2 6
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
S 2550 4550 1600 900 
U 5B2A1299
F0 "Level2" 50
F1 "Level2.sch" 50
F2 "out_level_2" O R 4150 5100 50 
$EndSheet
$Comp
L Device:R R4
U 1 1 5B2A4B5E
P 2550 3100
F 0 "R4" H 2650 3150 50  0000 C CNN
F 1 "R" H 2650 3050 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal" V 2480 3100 50  0001 C CNN
F 3 "~" H 2550 3100 50  0001 C CNN
	1    2550 3100
	1    0    0    -1  
$EndComp
$Comp
L Device:R R5
U 1 1 5B2A4B6D
P 2550 4000
F 0 "R5" H 2650 4050 50  0000 C CNN
F 1 "R" H 2650 3950 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal" V 2480 4000 50  0001 C CNN
F 3 "~" H 2550 4000 50  0001 C CNN
	1    2550 4000
	1    0    0    -1  
$EndComp
Wire Wire Line
	3000 3650 2900 3650
Wire Wire Line
	2900 3650 2900 3800
Wire Wire Line
	2900 3800 3700 3800
Wire Wire Line
	3700 3800 3700 3550
Wire Wire Line
	3700 3550 3600 3550
$Comp
L power:+5V #PWR07
U 1 1 5B2A4C07
P 2550 2850
F 0 "#PWR07" H 2550 2700 50  0001 C CNN
F 1 "+5V" H 2550 2990 50  0000 C CNN
F 2 "" H 2550 2850 50  0001 C CNN
F 3 "" H 2550 2850 50  0001 C CNN
	1    2550 2850
	1    0    0    -1  
$EndComp
$Comp
L Passives:GND #PWR08
U 1 1 5B2A4C39
P 2550 4250
F 0 "#PWR08" H 2550 4100 50  0001 C CNN
F 1 "GND" H 2700 4200 50  0001 C CNN
F 2 "" H 2550 4250 50  0001 C CNN
F 3 "" H 2550 4250 50  0001 C CNN
	1    2550 4250
	1    0    0    -1  
$EndComp
Wire Wire Line
	2550 4250 2550 4150
Wire Wire Line
	2550 3850 2550 3450
Wire Wire Line
	2550 3450 3000 3450
Connection ~ 2550 3450
Wire Wire Line
	2550 2850 2550 2950
Wire Wire Line
	2550 3250 2550 3450
Text HLabel 3700 3550 2    50   Output ~ 0
out_level_1
Wire Wire Line
	4150 5100 4450 5100
Text HLabel 4450 5100 2    50   Output ~ 0
out_level_2
$Comp
L Amplifier_Operational:LM324 U1
U 3 1 5C8869E5
P 3300 3550
F 0 "U1" H 3300 3750 50  0000 L CNN
F 1 "LM324" H 3300 3350 50  0000 L CNN
F 2 "" H 3250 3650 50  0001 C CNN
F 3 "http://www.ti.com/lit/ds/symlink/lm2902-n.pdf" H 3350 3750 50  0001 C CNN
	3    3300 3550
	1    0    0    -1  
$EndComp
$Sheet
S 2550 1300 1500 850 
U 5C9CDC4B
F0 "Level2b" 50
F1 "Level2.sch" 50
$EndSheet
$Sheet
S 4500 1300 1700 850 
U 5CB4DE53
F0 "Level3a" 50
F1 "Level3.sch" 50
$EndSheet
$Sheet
S 4500 3100 1700 850 
U 5CB51184
F0 "Level3b" 50
F1 "Level3.sch" 50
$EndSheet
$EndSCHEMATC
