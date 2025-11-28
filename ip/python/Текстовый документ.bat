@echo off
chcp 65001 > nul
title Мультипротокольный тестер сети
color 0A

:menu
cls
echo ========================================
echo    УЧЕБНЫЙ СЕТЕВОЙ ТЕСТЕР
echo ========================================
echo.
echo 1 - Ping флуд (ICMP)
echo 2 - TCP подключения
echo 3 - UDP тест
echo 4 - Комбинированная атака
echo 5 - Выход
echo.
set /p choice=Выберите вариант: 

if "%choice%"=="1" goto ping_flood
if "%choice%"=="2" goto tcp_test
if "%choice%"=="3" goto udp_test
if "%choice%"=="4" goto combined
if "%choice%"=="5" exit

goto menu

:ping_flood
cls
echo === PING FLOOD TEST ===
set /p target_ip=Введите IP: 
set /p count=Количество пакетов: 
set /p delay=Задержка (мс): 
set packets=0

echo Запуск ICMP теста...
:ping_loop
if %packets% geq %count% goto ping_end
ping -n 1 -l 1024 %target_ip% > nul
set /a packets+=1
echo ICMP пакет %packets%/%count% отправлен
timeout /t 0 /nobreak > nul
goto ping_loop

:ping_end
echo Тест завершен!
pause
goto menu

:tcp_test
cls
echo === TCP CONNECTION TEST ===
set /p target_ip=Введите IP: 
set /p target_port=Введите порт: 
set /p count=Количество попыток: 
set attempts=0

echo Запуск TCP теста...
:tcp_loop
if %attempts% geq %count% goto tcp_end
echo Попытка TCP подключения %attempts%/%count%
powershell -Command "Test-NetConnection -ComputerName %target_ip% -Port %target_port% -InformationLevel Quiet"
set /a attempts+=1
timeout /t 1 /nobreak > nul
goto tcp_loop

:tcp_end
echo TCP тест завершен!
pause
goto menu

:udp_test
cls
echo === UDP TEST ===
echo UDP тест требует специальных утилит
echo Используйте другие методы для UDP
pause
goto menu

:combined
cls
echo === КОМБИНИРОВАННЫЙ ТЕСТ ===
set /p target_ip=Введите IP: 
set /p count=Количество итераций: 

echo Запуск комбинированного теста...
set iteration=0

:comb_loop
if %iteration% geq %count% goto comb_end

echo Итерация %iteration%/%count%
echo - ICMP...
ping -n 1 %target_ip% > nul
echo - TCP...
powershell -Command "Test-NetConnection -ComputerName %target_ip% -Port 80 -InformationLevel Quiet" > nul

set /a iteration+=1
goto comb_loop

:comb_end
echo Комбинированный тест завершен!
pause
goto menu