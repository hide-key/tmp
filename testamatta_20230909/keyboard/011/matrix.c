#include "matrix.h"
#include "wait.h"
#include "quantum.h"

#define ROWS 4
#define COLS 6

// 単一の行・列ピンを定義
static const pin_t row_pins[ROWS] = { GP1, GP2, GP3, GP4 };
static const pin_t col_pins[COLS] = { GP6, GP7, GP26, GP27, GP28, GP29 };

// 二重の列ピンを定義（オプション）
static const pin_t col_pins_duplex[COLS] = { GP6, GP7, GP26, GP27, GP28, GP29 };

// 行の状態を保存するための配列
static matrix_row_t matrix[ROWS];

// 初期化
void matrix_init(void) {
    for (int i = 0; i < ROWS; i++) {
        setPinInputHigh(row_pins[i]);  // プルアップ
    }
    for (int i = 0; i < COLS; i++) {
        setPinOutput(col_pins[i]);  // 出力に設定
        setPinOutput(col_pins_duplex[i]);  // 二重の列も出力に設定（オプション）
    }
}

// マトリックススキャン
uint8_t matrix_scan(void) {
    for (uint8_t row = 0; row < ROWS; row++) {
        setPinOutput(row_pins[row]);  // 行を出力に設定
        writePinLow(row_pins[row]);  // 行をLOWに

        wait_us(1);  // 1us待機

        matrix_row_t cols = 0;
        for (uint8_t col = 0; col < COLS; col++) {
            // 列をHIGH, LOWに設定し、状態を読み取る
            writePinHigh(col_pins[col]);
            writePinLow(col_pins_duplex[col]);

            if (readPin(col_pins[col]) == 0 || readPin(col_pins_duplex[col]) == 0) {
                cols |= 1UL << col;  // 対応するビットを1に
            }

            // 列を元に戻す
            writePinLow(col_pins[col]);
            writePinHigh(col_pins_duplex[col]);

            wait_us(1);  // 1us待機
        }

        // 状態を保存
        matrix[row] = cols;

        // 行を入力に戻す（プルアップ）
        setPinInputHigh(row_pins[row]);
    }
    return 1;  // 成功
}

// 指定した行の状態を取得
matrix_row_t matrix_get_row(uint8_t row) {
    if (row < ROWS) {
        return matrix[row];
    }
    return 0;
}

// カスタムのunselect遅延処理（オプション）
void matrix_output_unselect_delay(uint8_t line, bool key_pressed) {
    // 何もしない
}
