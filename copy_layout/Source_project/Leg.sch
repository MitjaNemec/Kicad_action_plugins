EESchema Schematic File Version 4
LIBS:multiple_hierarchy-cache
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 2 14
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
S 4100 1450 1850 1350
U 5B767FF2
F0 "Power+" 50
F1 "Power.sch" 50
F2 "OUT" I R 5950 2100 50 
F3 "QH" I L 4100 1950 50 
F4 "Ql" I L 4100 2100 50 
$EndSheet
$Sheet
S 4150 3400 1800 1300
U 5B767FF5
F0 "Sensor" 50
F1 "Sensor.sch" 50
F2 "IN" I R 5950 3700 50 
F3 "OUT" O R 5950 4000 50 
F4 "Current" O L 4150 3800 50 
$EndSheet
Wire Wire Line
	5950 3700 6250 3700
Wire Wire Line
	6250 3700 6250 2100
Wire Wire Line
	6250 2100 5950 2100
Wire Wire Line
	5950 4000 6850 4000
Text HLabel 3700 1950 0    50   Input ~ 0
QH
Text HLabel 3700 2100 0    50   Input ~ 0
QL
Text HLabel 3700 3800 0    50   Output ~ 0
Current
Wire Wire Line
	3700 1950 3850 1950
Wire Wire Line
	4100 2100 3950 2100
Wire Wire Line
	3700 3800 4150 3800
$Sheet
S 4150 5200 1850 1350
U 5B772791
F0 "Power-" 50
F1 "Power.sch" 50
F2 "OUT" I R 6000 5850 50 
F3 "QH" I L 4150 5700 50 
F4 "Ql" I L 4150 5850 50 
$EndSheet
Wire Wire Line
	4150 5700 3950 5700
Wire Wire Line
	3950 5700 3950 2100
Connection ~ 3950 2100
Wire Wire Line
	3950 2100 3700 2100
Wire Wire Line
	3850 1950 3850 5850
Wire Wire Line
	3850 5850 4150 5850
Connection ~ 3850 1950
Wire Wire Line
	3850 1950 4100 1950
Wire Wire Line
	6000 5850 6850 5850
$Comp
L Connector:Pusa_4mm J201
U 1 1 5B772913
P 7050 4000
AR Path="/5B767FE4/5B772913" Ref="J201"  Part="1" 
AR Path="/5B76D023/5B772913" Ref="J601"  Part="1" 
AR Path="/5B76D031/5B772913" Ref="J1001"  Part="1" 
F 0 "J201" H 7129 4042 50  0000 L CNN
F 1 "Pusa_4mm" H 7129 3951 50  0000 L CNN
F 2 "Connector:Pusa_4mm" H 7125 3950 50  0001 L CNN
F 3 "~" H 7050 4000 50  0001 C CNN
	1    7050 4000
	1    0    0    -1  
$EndComp
$Comp
L Connector:Pusa_4mm J202
U 1 1 5B77299E
P 7050 5850
AR Path="/5B767FE4/5B77299E" Ref="J202"  Part="1" 
AR Path="/5B76D023/5B77299E" Ref="J602"  Part="1" 
AR Path="/5B76D031/5B77299E" Ref="J1002"  Part="1" 
F 0 "J202" H 7129 5892 50  0000 L CNN
F 1 "Pusa_4mm" H 7129 5801 50  0000 L CNN
F 2 "Connector:Pusa_4mm" H 7125 5800 50  0001 L CNN
F 3 "~" H 7050 5850 50  0001 C CNN
	1    7050 5850
	1    0    0    -1  
$EndComp
$EndSCHEMATC
