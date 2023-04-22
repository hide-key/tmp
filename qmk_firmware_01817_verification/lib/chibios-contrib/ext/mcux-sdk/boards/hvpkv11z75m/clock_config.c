/*
 * Copyright (c) 2015, Freescale Semiconductor, Inc.
 * Copyright 2016-2017 NXP
 * All rights reserved.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */
/***********************************************************************************************************************
 * This file was generated by the MCUXpresso Config Tools. Any manual edits made to this file
 * will be overwritten if the respective MCUXpresso Config Tools is used to update this file.
 **********************************************************************************************************************/
/*
 * How to setup clock using clock driver functions:
 *
 * 1. CLOCK_SetSimSafeDivs, to make sure core clock, bus clock, flexbus clock
 *    and flash clock are in allowed range during clock mode switch.
 *
 * 2. Call CLOCK_Osc0Init to setup OSC clock, if it is used in target mode.
 *
 * 3. Set MCG configuration, MCG includes three parts: FLL clock, PLL clock and
 *    internal reference clock(MCGIRCLK). Follow the steps to setup:
 *
 *    1). Call CLOCK_BootToXxxMode to set MCG to target mode.
 *
 *    2). If target mode is FBI/BLPI/PBI mode, the MCGIRCLK has been configured
 *        correctly. For other modes, need to call CLOCK_SetInternalRefClkConfig
 *        explicitly to setup MCGIRCLK.
 *
 *    3). Don't need to configure FLL explicitly, because if target mode is FLL
 *        mode, then FLL has been configured by the function CLOCK_BootToXxxMode,
 *        if the target mode is not FLL mode, the FLL is disabled.
 *
 *    4). If target mode is PEE/PBE/PEI/PBI mode, then the related PLL has been
 *        setup by CLOCK_BootToXxxMode. In FBE/FBI/FEE/FBE mode, the PLL could
 *        be enabled independently, call CLOCK_EnablePll0 explicitly in this case.
 *
 * 4. Call CLOCK_SetSimConfig to set the clock configuration in SIM.
 */

/* clang-format off */
/* TEXT BELOW IS USED AS SETTING FOR TOOLS *************************************
!!GlobalInfo
product: Clocks v4.0
processor: MKV11Z128xxx7
package_id: MKV11Z128VLF7
mcu_data: ksdk2_0
processor_version: 0.0.4
 * BE CAREFUL MODIFYING THIS COMMENT - IT IS YAML SETTINGS FOR TOOLS **********/
/* clang-format on */

#include "fsl_smc.h"
#include "clock_config.h"

/*******************************************************************************
 * Definitions
 ******************************************************************************/
#define OSC_CAP0P 0U             /*!< Oscillator 0pF capacitor load */
#define OSC_ER_CLK_DISABLE 0U    /*!< Disable external reference clock */
#define SIM_OSC32KSEL_LPO_CLK 3U /*!< OSC32KSEL select: LPO clock */

/*******************************************************************************
 * Variables
 ******************************************************************************/
/* System clock frequency. */
extern uint32_t SystemCoreClock;

/*******************************************************************************
 * Code
 ******************************************************************************/
/*FUNCTION**********************************************************************
 *
 * Function Name : CLOCK_CONFIG_FllStableDelay
 * Description   : This function is used to delay for FLL stable.
 *
 *END**************************************************************************/
static void CLOCK_CONFIG_FllStableDelay(void)
{
    uint32_t i = 30000U;
    while (i--)
    {
        __NOP();
    }
}

/*******************************************************************************
 ************************ BOARD_InitBootClocks function ************************
 ******************************************************************************/
void BOARD_InitBootClocks(void)
{
    BOARD_BootClockRUN();
}

/*******************************************************************************
 ********************** Configuration BOARD_BootClockRUN ***********************
 ******************************************************************************/
/* clang-format off */
/* TEXT BELOW IS USED AS SETTING FOR TOOLS *************************************
!!Configuration
name: BOARD_BootClockRUN
called_from_default_init: true
outputs:
- {id: Bus_clock.outFreq, value: 20.97152 MHz}
- {id: Core_clock.outFreq, value: 62.91456 MHz}
- {id: ERCLK32K.outFreq, value: 1 kHz}
- {id: LPO_clock.outFreq, value: 1 kHz}
- {id: MCGFLLCLK.outFreq, value: 62.91456 MHz}
- {id: MCGIRCLK.outFreq, value: 32.768 kHz}
- {id: System_clock.outFreq, value: 62.91456 MHz}
settings:
- {id: MCG.FCRDIV.scale, value: '1', locked: true}
- {id: MCG.FLL_mul.scale, value: '1920', locked: true}
- {id: MCG.FRDIV.scale, value: '256'}
- {id: MCG_C1_IRCLKEN_CFG, value: Enabled}
- {id: MCG_C2_OSC_MODE_CFG, value: ModeOscLowPower}
- {id: MCG_C2_RANGE0_CFG, value: Very_high}
- {id: MCG_C2_RANGE0_FRDIV_CFG, value: Very_high}
- {id: OSC_CR_ERCLKEN_CFG, value: Enabled}
- {id: SIM.CLKOUTSEL.sel, value: SIM.OUTDIV4}
- {id: SIM.FTMFFCLKSEL.sel, value: OSC.OSCERCLK}
- {id: SIM.OSC32KSEL.sel, value: PMC.LPOCLK}
- {id: SIM.OUTDIV1.scale, value: '1', locked: true}
- {id: SIM.OUTDIV4.scale, value: '3', locked: true}
- {id: SIM.OUTDIV5.scale, value: '1'}
sources:
- {id: OSC.OSC.outFreq, value: 10 MHz}
 * BE CAREFUL MODIFYING THIS COMMENT - IT IS YAML SETTINGS FOR TOOLS **********/
/* clang-format on */

/*******************************************************************************
 * Variables for BOARD_BootClockRUN configuration
 ******************************************************************************/
const mcg_config_t mcgConfig_BOARD_BootClockRUN = {
    .mcgMode         = kMCG_ModeFEI,      /* FEI - FLL Engaged Internal */
    .irclkEnableMode = kMCG_IrclkEnable,  /* MCGIRCLK enabled, MCGIRCLK disabled in STOP mode */
    .ircs            = kMCG_IrcSlow,      /* Slow internal reference clock selected */
    .fcrdiv          = 0x0U,              /* Fast IRC divider: divided by 1 */
    .frdiv           = 0x3U,              /* FLL reference clock divider: divided by 256 */
    .drs             = kMCG_DrsMidHigh,   /* Mid-High frequency range */
    .dmx32           = kMCG_Dmx32Default, /* DCO has a default range of 25% */
};
const sim_clock_config_t simConfig_BOARD_BootClockRUN = {
    .er32kSrc = SIM_OSC32KSEL_LPO_CLK, /* OSC32KSEL select: LPO clock */
    .clkdiv1  = 0x20000U,              /* SIM_CLKDIV1 - OUTDIV1: /1, OUTDIV4: /3, OUTDIV5: /1, disabled */
};
const osc_config_t oscConfig_BOARD_BootClockRUN = {
    .freq        = 0U,                   /* Oscillator frequency: 0Hz */
    .capLoad     = (OSC_CAP0P),          /* Oscillator capacity load: 0pF */
    .workMode    = kOSC_ModeOscLowPower, /* Oscillator low power */
    .oscerConfig = {
        .enableMode =
            kOSC_ErClkEnable, /* Enable external reference clock, disable external reference clock in STOP mode */
    }};

/*******************************************************************************
 * Code for BOARD_BootClockRUN configuration
 ******************************************************************************/
void BOARD_BootClockRUN(void)
{
    /* Set the system clock dividers in SIM to safe value. */
    CLOCK_SetSimSafeDivs();
    /* Set MCG to FEI mode. */
#if FSL_CLOCK_DRIVER_VERSION >= MAKE_VERSION(2, 2, 0)
    CLOCK_BootToFeiMode(mcgConfig_BOARD_BootClockRUN.dmx32, mcgConfig_BOARD_BootClockRUN.drs,
                        CLOCK_CONFIG_FllStableDelay);
#else
    CLOCK_BootToFeiMode(mcgConfig_BOARD_BootClockRUN.drs, CLOCK_CONFIG_FllStableDelay);
#endif
    /* Configure the Internal Reference clock (MCGIRCLK). */
    CLOCK_SetInternalRefClkConfig(mcgConfig_BOARD_BootClockRUN.irclkEnableMode, mcgConfig_BOARD_BootClockRUN.ircs,
                                  mcgConfig_BOARD_BootClockRUN.fcrdiv);
    /* Set the clock configuration in SIM module. */
    CLOCK_SetSimConfig(&simConfig_BOARD_BootClockRUN);
    /* Set SystemCoreClock variable. */
    SystemCoreClock = BOARD_BOOTCLOCKRUN_CORE_CLOCK;
}

/*******************************************************************************
 ********************* Configuration BOARD_BootClockVLPR ***********************
 ******************************************************************************/
/* clang-format off */
/* TEXT BELOW IS USED AS SETTING FOR TOOLS *************************************
!!Configuration
name: BOARD_BootClockVLPR
outputs:
- {id: Bus_clock.outFreq, value: 800 kHz}
- {id: Core_clock.outFreq, value: 4 MHz}
- {id: ERCLK32K.outFreq, value: 1 kHz}
- {id: LPO_clock.outFreq, value: 1 kHz}
- {id: MCGIRCLK.outFreq, value: 4 MHz}
- {id: System_clock.outFreq, value: 4 MHz}
settings:
- {id: MCGMode, value: BLPI}
- {id: powerMode, value: VLPR}
- {id: MCG.CLKS.sel, value: MCG.IRCS}
- {id: MCG.FCRDIV.scale, value: '1', locked: true}
- {id: MCG.FRDIV.scale, value: '32'}
- {id: MCG.IRCS.sel, value: MCG.FCRDIV}
- {id: MCG_C1_IRCLKEN_CFG, value: Enabled}
- {id: MCG_C2_OSC_MODE_CFG, value: ModeOscLowPower}
- {id: MCG_C2_RANGE0_CFG, value: Very_high}
- {id: MCG_C2_RANGE0_FRDIV_CFG, value: Very_high}
- {id: SIM.OSC32KSEL.sel, value: PMC.LPOCLK}
- {id: SIM.OUTDIV1.scale, value: '1', locked: true}
- {id: SIM.OUTDIV4.scale, value: '5'}
- {id: SIM.OUTDIV5.scale, value: '1', locked: true}
sources:
- {id: OSC.OSC.outFreq, value: 10 MHz}
 * BE CAREFUL MODIFYING THIS COMMENT - IT IS YAML SETTINGS FOR TOOLS **********/
/* clang-format on */

/*******************************************************************************
 * Variables for BOARD_BootClockVLPR configuration
 ******************************************************************************/
const mcg_config_t mcgConfig_BOARD_BootClockVLPR = {
    .mcgMode         = kMCG_ModeBLPI,     /* BLPI - Bypassed Low Power Internal */
    .irclkEnableMode = kMCG_IrclkEnable,  /* MCGIRCLK enabled, MCGIRCLK disabled in STOP mode */
    .ircs            = kMCG_IrcFast,      /* Fast internal reference clock selected */
    .fcrdiv          = 0x0U,              /* Fast IRC divider: divided by 1 */
    .frdiv           = 0x0U,              /* FLL reference clock divider: divided by 32 */
    .drs             = kMCG_DrsLow,       /* Low frequency range */
    .dmx32           = kMCG_Dmx32Default, /* DCO has a default range of 25% */
};
const sim_clock_config_t simConfig_BOARD_BootClockVLPR = {
    .er32kSrc = SIM_OSC32KSEL_LPO_CLK, /* OSC32KSEL select: LPO clock */
    .clkdiv1  = 0x40000U,              /* SIM_CLKDIV1 - OUTDIV1: /1, OUTDIV4: /5, OUTDIV5: /1, disabled */
};
const osc_config_t oscConfig_BOARD_BootClockVLPR = {
    .freq        = 0U,                   /* Oscillator frequency: 0Hz */
    .capLoad     = (OSC_CAP0P),          /* Oscillator capacity load: 0pF */
    .workMode    = kOSC_ModeOscLowPower, /* Oscillator low power */
    .oscerConfig = {
        .enableMode = OSC_ER_CLK_DISABLE, /* Disable external reference clock */
    }};

/*******************************************************************************
 * Code for BOARD_BootClockVLPR configuration
 ******************************************************************************/
void BOARD_BootClockVLPR(void)
{
    /* Set the system clock dividers in SIM to safe value. */
    CLOCK_SetSimSafeDivs();
    /* Set MCG to BLPI mode. */
    CLOCK_BootToBlpiMode(mcgConfig_BOARD_BootClockVLPR.fcrdiv, mcgConfig_BOARD_BootClockVLPR.ircs,
                         mcgConfig_BOARD_BootClockVLPR.irclkEnableMode);
    /* Set the clock configuration in SIM module. */
    CLOCK_SetSimConfig(&simConfig_BOARD_BootClockVLPR);
    /* Set VLPR power mode. */
    SMC_SetPowerModeProtection(SMC, kSMC_AllowPowerModeAll);
#if (defined(FSL_FEATURE_SMC_HAS_LPWUI) && FSL_FEATURE_SMC_HAS_LPWUI)
    SMC_SetPowerModeVlpr(SMC, false);
#else
    SMC_SetPowerModeVlpr(SMC);
#endif
    while (SMC_GetPowerModeState(SMC) != kSMC_PowerStateVlpr)
    {
    }
    /* Set SystemCoreClock variable. */
    SystemCoreClock = BOARD_BOOTCLOCKVLPR_CORE_CLOCK;
}
