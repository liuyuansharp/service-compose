#include <immintrin.h>
#include <stdio.h>

int main() {
    // 使用 AVX-512 指令初始化两个寄存器并执行加法
    __m512 a = _mm512_set1_ps(1.0f);
    __m512 b = _mm512_set1_ps(2.0f);
    __m512 c = _mm512_add_ps(a, b);

    float res[16];
    _mm512_storeu_ps(res, c);

    printf("AVX-512 result: %.2f %.2f %.2f ...\n", res[0], res[1], res[2]);
    return 0;
}
