@echo off
md "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos" 2>nul
md "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\sentinel" 2>nul
md "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\inquisitor" 2>nul
md "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\shared" 2>nul
md "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\db" 2>nul
md "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\tests" 2>nul
echo x>"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\__init__.py"
echo x>"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\sentinel\__init__.py"
echo x>"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\inquisitor\__init__.py"
echo x>"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\shared\__init__.py"
echo CREATED>"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\_flag.txt"
