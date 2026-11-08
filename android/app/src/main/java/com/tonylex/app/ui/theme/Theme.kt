package com.tonylex.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val TxViolet = Color(0xFF7C3AED)
val TxViolet2 = Color(0xFF6D28D9)
val TxSoftBg = Color(0xFFEEEDF5)
val TxInk = Color(0xFF1A1630)
val TxMuted = Color(0xFF6B6685)
val TxDark = Color(0xFF1B1629)
val TxDark2 = Color(0xFF231E36)
val TxSurface = Color(0xFFFFFFFF)

private val LightColors = lightColorScheme(
    primary = TxViolet,
    secondary = Color(0xFFA78BFA),
    background = TxSoftBg,
    surface = TxSurface,
    onPrimary = Color.White,
    onBackground = TxInk,
    onSurface = TxInk,
    surfaceVariant = Color(0xFFEFEDF7),
)

private val DarkColors = darkColorScheme(
    primary = Color(0xFFA78BFA),
    secondary = TxViolet,
    background = Color(0xFF0C1020),
    surface = TxDark2,
    onPrimary = Color.White,
    onBackground = Color(0xFFF5F3FF),
    onSurface = Color(0xFFF5F3FF),
)

@Composable
fun TonylexTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (isSystemInDarkTheme()) DarkColors else LightColors,
        content = content,
    )
}
