#pragma once

#include "quantum.h"

// 通常のマトリクスの初期化
void matrix_init(void);

// マトリクスのスキャン処理
uint8_t matrix_scan(void);

// 指定した行のマトリクスデータを取得
matrix_row_t matrix_get_row(uint8_t row);

// 独自に追加された関数のプロトタイプ宣言
void matrix_output_unselect_delay(uint8_t line, bool key_pressed);

// その他必要な関数があればこちらに追加
