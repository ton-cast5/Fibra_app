package com.tonylex.app.ui.screens

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import coil.compose.rememberAsyncImagePainter
import coil.request.ImageRequest
import kotlinx.coroutines.delay

@Composable
fun SplashScreen(onFinished: () -> Unit) {
    var showLogo by remember { mutableStateOf(false) }
    var showWord by remember { mutableStateOf(false) }
    val logoScale by animateFloatAsState(
        targetValue = if (showLogo) 1f else 0.82f,
        animationSpec = tween(900),
        label = "logoScale",
    )
    val logoAlpha by animateFloatAsState(
        targetValue = if (showLogo) 1f else 0f,
        animationSpec = tween(900),
        label = "logoAlpha",
    )
    val wordAlpha by animateFloatAsState(
        targetValue = if (showWord) 1f else 0f,
        animationSpec = tween(700),
        label = "wordAlpha",
    )

    LaunchedEffect(Unit) {
        showLogo = true
        delay(1100)
        showWord = true
        delay(1500)
        onFinished()
    }

    val ctx = LocalContext.current
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(28.dp),
            modifier = Modifier.padding(24.dp),
        ) {
            Image(
                painter = rememberAsyncImagePainter(
                    ImageRequest.Builder(ctx).data("file:///android_asset/brand/logo-tonylex.png").build(),
                ),
                contentDescription = "TONYLEX",
                modifier = Modifier
                    .width(200.dp)
                    .scale(logoScale)
                    .alpha(logoAlpha),
            )
            Image(
                painter = rememberAsyncImagePainter(
                    ImageRequest.Builder(ctx).data("file:///android_asset/brand/tonylex-wordmark.png").build(),
                ),
                contentDescription = null,
                modifier = Modifier
                    .fillMaxWidth(0.75f)
                    .alpha(wordAlpha),
            )
        }
    }
}
