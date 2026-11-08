package com.tonylex.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Violet = Color(0xFF7C3AED)
private val VioletSoft = Color(0xFFA78BFA)
private val Ink = Color(0xFF1E1B2E)
private val SoftBg = Color(0xFFF4F2FB)

private val LightColors = lightColorScheme(
    primary = Violet,
    secondary = VioletSoft,
    background = SoftBg,
    surface = Color.White,
    onPrimary = Color.White,
    onBackground = Ink,
    onSurface = Ink,
)

private val DarkColors = darkColorScheme(
    primary = VioletSoft,
    secondary = Violet,
    background = Color(0xFF0C1222),
    surface = Color(0xFF151D2E),
    onPrimary = Color.White,
)

@Composable
fun TonylexTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (isSystemInDarkTheme()) DarkColors else LightColors,
        content = content,
    )
}
