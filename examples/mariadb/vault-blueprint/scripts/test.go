package main

import "fmt"
import "os"

func main() {
	fmt.Printf("ctx socket url = %s\n", os.Getenv("CTX_SOCKET_URL"))
}
