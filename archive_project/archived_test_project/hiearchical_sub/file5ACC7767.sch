EESchema Schematic File Version 4
LIBS:archive_test_project-cache
EELAYER 26 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 4 4
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
L power:+15V #PWR?
U 1 1 5BBCAF4C
P 3600 2450
F 0 "#PWR?" H 3600 2300 50  0001 C CNN
F 1 "+15V" H 3600 2590 50  0000 C CNN
F 2 "" H 3600 2450 50  0001 C CNN
F 3 "" H 3600 2450 50  0001 C CNN
	1    3600 2450
	1    0    0    -1  
$EndComp
$Comp
L Passives:C1206 C?
U 1 1 5BBCAF9F
P 3600 2650
F 0 "C?" H 3700 2700 50  0000 L CNN
F 1 "C1206" H 3700 2600 50  0000 L CNN
F 2 "Passives:C1206M" H 3650 2550 50  0001 L CNN
F 3 "" H 3600 2650 50  0001 C CNN
	1    3600 2650
	1    0    0    -1  
$EndComp
Wire Wire Line
	3600 2550 3600 2450
$Comp
L power:GND #PWR?
U 1 1 5BBCB01A
P 3600 2900
F 0 "#PWR?" H 3600 2650 50  0001 C CNN
F 1 "GND" H 3600 2750 50  0000 C CNN
F 2 "" H 3600 2900 50  0001 C CNN
F 3 "" H 3600 2900 50  0001 C CNN
	1    3600 2900
	1    0    0    -1  
$EndComp
Wire Wire Line
	3600 2900 3600 2750
$EndSCHEMATC
