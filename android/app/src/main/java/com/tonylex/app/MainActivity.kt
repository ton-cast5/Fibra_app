package com.tonylex.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import com.tonylex.app.ui.screens.HomeScreen
import com.tonylex.app.ui.screens.LoginScreen
import com.tonylex.app.ui.screens.SplashScreen
import com.tonylex.app.ui.theme.TonylexTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val app = application as TonylexApp
        setContent {
            TonylexTheme {
                var showSplash by remember { mutableStateOf(true) }
                var loggedIn by remember { mutableStateOf(app.tokenStore.isLoggedIn()) }

                when {
                    showSplash -> SplashScreen(onFinished = { showSplash = false })
                    !loggedIn -> LoginScreen(onLoggedIn = { loggedIn = true })
                    else -> HomeScreen(onLogout = { loggedIn = false })
                }
            }
        }
    }
}
