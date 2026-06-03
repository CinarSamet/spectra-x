/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body with Anti-Lock RSSI Pipeline
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "i2c.h"
#include "spi.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
/* USER CODE END Includes */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
uint8_t CC1101_ReadRegister(uint8_t reg_addr);
void CC1101_Init(void);
void CC1101_SendCommand(uint8_t command);
void CC1101_WriteRegister(uint8_t reg_addr, uint8_t value);
int CC1101_GetRSSI(void);
/* USER CODE END PFP */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* MCU Configuration--------------------------------------------------------*/
  HAL_Init();
  SystemClock_Config();

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_I2C1_Init();
  MX_SPI1_Init();
  MX_USART1_UART_Init();

  /* USER CODE BEGIN 2 */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  GPIO_InitTypeDef GPIO_InitStructPrivate = {0};
  GPIO_InitStructPrivate.Pin = GPIO_PIN_13;
  GPIO_InitStructPrivate.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStructPrivate.Pull = GPIO_NOPULL;
  GPIO_InitStructPrivate.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStructPrivate);

  CC1101_Init();

  printf("\r\n--- CALIBRATING RF ENVIRONMENT... ---\r\n");

  int32_t rssi_accumulator = 0;
  int baseline_rssi = -100;
  int calibration_samples = 50;

  for(int i = 0; i < calibration_samples; i++) {
      rssi_accumulator += CC1101_GetRSSI();
      HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
      HAL_Delay(100);
  }

  baseline_rssi = rssi_accumulator / calibration_samples;
  printf("CALIBRATION DONE. BASELINE RSSI: %d dBm\r\n", baseline_rssi);

  int jamming_threshold = baseline_rssi + 8;

  int anomaly_counter = 0;
  char* system_status = "NORMAL";
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  /* Infinite loop */
    /* USER CODE BEGIN WHILE */
    while (1)
    {
    	        uint8_t rx_cmd;
    	        if (HAL_UART_Receive(&huart1, &rx_cmd, 1, 10) == HAL_OK) {

    	            if (rx_cmd == 'H') {
    	                CC1101_SendCommand(0x36); // SIDLE
    	                CC1101_WriteRegister(0x0D, 0x10); // FREQ2
    	                CC1101_WriteRegister(0x0E, 0xB1); // FREQ1
    	                CC1101_WriteRegister(0x0F, 0x3B); // FREQ0 (434 MHz)
    	                CC1101_SendCommand(0x34); // SRX
    	                printf("\r\nHOPPED TO 434 MHz\r\n");
    	            }
    	            else if (rx_cmd == 'B') {
    	                CC1101_SendCommand(0x36); // SIDLE
    	                CC1101_WriteRegister(0x0D, 0x10); // FREQ2
    	                CC1101_WriteRegister(0x0E, 0xA7); // FREQ1
    	                CC1101_WriteRegister(0x0F, 0x62); // FREQ0 (433 MHz)
    	                CC1101_SendCommand(0x34); // SRX
    	                printf("\r\nRETURNED TO BASE (433 MHz)\r\n");
    	            }
    	        }

        int rssi_dbm = CC1101_GetRSSI();

        if (rssi_dbm > jamming_threshold) {
            anomaly_counter++;
            if (anomaly_counter >= 5) {
                system_status = "JAMMING_ATTACK";
                HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);
            }
        } else {
            if (anomaly_counter > 0) anomaly_counter--;
            if (anomaly_counter == 0) {
                system_status = "NORMAL";
                HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_SET);
            }
        }

        printf("RSSI:%d,STATUS:%s\r\n", rssi_dbm, system_status);

        HAL_Delay(80);
      /* USER CODE END WHILE */
    } }

int CC1101_GetRSSI(void) {

    CC1101_SendCommand(0x36); // SIDLE


    CC1101_SendCommand(0x3A); // SFRX


    CC1101_SendCommand(0x34); // SRX


    HAL_Delay(5);

    uint8_t raw = CC1101_ReadRegister(0x34);
    int dbm = (raw >= 128) ? (((raw - 256) / 2) - 74) : ((raw / 2) - 74);

    return dbm;
}

void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK) { Error_Handler(); }
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK|RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;
  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK) { Error_Handler(); }
}

/* USER CODE BEGIN 4 */
int __io_putchar(int ch) {
    HAL_UART_Transmit(&huart1, (uint8_t *)&ch, 1, HAL_MAX_DELAY);
    return ch;
}

void CC1101_SendCommand(uint8_t command) {
    HAL_GPIO_WritePin(GPIOA, CC1101_CS_Pin, GPIO_PIN_RESET);
    HAL_SPI_Transmit(&hspi1, &command, 1, 10);
    HAL_GPIO_WritePin(GPIOA, CC1101_CS_Pin, GPIO_PIN_SET);
}

void CC1101_WriteRegister(uint8_t reg_addr, uint8_t value) {
    HAL_GPIO_WritePin(GPIOA, CC1101_CS_Pin, GPIO_PIN_RESET);
    HAL_SPI_Transmit(&hspi1, &reg_addr, 1, 10);
    HAL_SPI_Transmit(&hspi1, &value, 1, 10);
    HAL_GPIO_WritePin(GPIOA, CC1101_CS_Pin, GPIO_PIN_SET);
}

uint8_t CC1101_ReadRegister(uint8_t reg_addr) {
    uint8_t send_byte = reg_addr | 0x80;
    if (reg_addr >= 0x30) { send_byte |= 0x40; }
    uint8_t receive_byte = 0;
    HAL_GPIO_WritePin(GPIOA, CC1101_CS_Pin, GPIO_PIN_RESET);
    HAL_SPI_Transmit(&hspi1, &send_byte, 1, 10);
    uint8_t dummy = 0;
    HAL_SPI_TransmitReceive(&hspi1, &dummy, &receive_byte, 1, 10);
    HAL_GPIO_WritePin(GPIOA, CC1101_CS_Pin, GPIO_PIN_SET);
    return receive_byte;
}

void CC1101_Init(void) {
    CC1101_SendCommand(0x30); // SRES
    HAL_Delay(10);
    CC1101_WriteRegister(0x12, 0x00); // MDMCFG2
    CC1101_WriteRegister(0x08, 0x00); // PKTCTRL0
    CC1101_WriteRegister(0x18, 0x18); // MCSM0
    CC1101_SendCommand(0x34);         // SRX
}
/* USER CODE END 4 */

void Error_Handler(void) { __disable_irq(); while (1) {} }
