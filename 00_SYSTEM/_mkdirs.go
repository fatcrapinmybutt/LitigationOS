package main

import (
	"fmt"
	"os"
)

func main() {
	dirs := []string{
		`C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\sentinel`,
		`C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\inquisitor`,
		`C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\shared`,
		`C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\db`,
		`C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\tests`,
	}
	for _, d := range dirs {
		err := os.MkdirAll(d, 0755)
		if err != nil {
			fmt.Printf("ERROR: %s: %v\n", d, err)
		} else {
			fmt.Printf("OK: %s\n", d)
		}
	}
	fmt.Println("DONE")
}
