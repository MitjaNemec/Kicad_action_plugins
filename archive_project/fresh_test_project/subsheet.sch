EESchema Schematic File Version 4
LIBS:archive_test_project-cache
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 2 4
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L Device:C C2
U 1 1 5ABA5ABB
P 5450 3800
F 0 "C2" H 5565 3846 50  0000 L CNN
F 1 "C" H 5565 3755 50  0000 L CNN
F 2 "Capacitor_SMD:C_1206_3216Metric" H 5488 3650 50  0001 C CNN
F 3 "~" H 5450 3800 50  0001 C CNN
	1    5450 3800
	1    0    0    -1  
$EndComp
$Comp
L Device:R R1
U 1 1 5ABA5B10
P 5200 3600
F 0 "R1" V 4993 3600 50  0000 C CNN
F 1 "R" V 5084 3600 50  0000 C CNN
F 2 "Resistor_SMD:R_1206_3216Metric" V 5130 3600 50  0001 C CNN
F 3 "~" H 5200 3600 50  0001 C CNN
	1    5200 3600
	0    1    1    0   
$EndComp
Wire Wire Line
	5050 3600 4850 3600
Wire Wire Line
	5350 3600 5450 3600
Wire Wire Line
	5450 3650 5450 3600
Connection ~ 5450 3600
Wire Wire Line
	5450 3600 5700 3600
$Comp
L power:GND #PWR09
U 1 1 5ABA5BCB
P 5450 4050
F 0 "#PWR09" H 5450 3800 50  0001 C CNN
F 1 "GND" H 5455 3877 50  0000 C CNN
F 2 "" H 5450 4050 50  0001 C CNN
F 3 "" H 5450 4050 50  0001 C CNN
	1    5450 4050
	1    0    0    -1  
$EndComp
Wire Wire Line
	5450 4050 5450 3950
Text HLabel 4850 3600 0    50   Input ~ 0
IN
Text HLabel 5700 3600 2    50   Output ~ 0
OUT
$EndSCHEMATC
