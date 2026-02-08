#!/bin/sh

gcc -O2 -mavx512f test_avx512.c -o test_avx512

./test_avx512