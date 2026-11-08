package com.tonylex.app.ui.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import coil.compose.rememberAsyncImagePainter
import coil.request.ImageRequest
import com.tonylex.app.TonylexApp
import kotlinx.coroutines.launch

@Composable
fun LoginScreen(onLoggedIn: () -> Unit) {
    val app = LocalContext.current.applicationContext as TonylexApp
    val scope = rememberCoroutineScope()
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var baseUrl by remember {
        mutableStateOf(
            app.tokenStore.apiBaseUrl
                ?: com.tonylex.app.BuildConfig.API_BASE_URL
        )
    }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val ctx = LocalContext.current

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Image(
            painter = rememberAsyncImagePainter(
                ImageRequest.Builder(ctx).data("file:///android_asset/brand/logo-tonylex.png").build(),
            ),
            contentDescription = null,
            modifier = Modifier.width(96.dp).padding(bottom = 12.dp),
        )
        Text("TONYLEX", style = MaterialTheme.typography.headlineMedium)
        Text(
            "Inicia sesión (requiere red la primera vez)",
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.padding(bottom = 20.dp),
        )

        Card(
            shape = RoundedCornerShape(24.dp),
            elevation = CardDefaults.cardElevation(6.dp),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = baseUrl,
                    onValueChange = { baseUrl = it },
                    label = { Text("URL API (https://...)") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                )
                OutlinedTextField(
                    value = username,
                    onValueChange = { username = it },
                    label = { Text("Usuario") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                )
                OutlinedTextField(
                    value = password,
                    onValueChange = { password = it },
                    label = { Text("Contraseña") },
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                )
                error?.let {
                    Text(it, color = MaterialTheme.colorScheme.error)
                }
                Button(
                    onClick = {
                        loading = true
                        error = null
                        scope.launch {
                            try {
                                if (baseUrl.isNotBlank()) {
                                    app.tokenStore.apiBaseUrl = baseUrl.trim()
                                }
                                app.rebuildGraph()
                                app.repository.login(username, password, null)
                                onLoggedIn()
                            } catch (e: Exception) {
                                error = e.message ?: "Error de login"
                            } finally {
                                loading = false
                            }
                        }
                    },
                    enabled = !loading && username.isNotBlank() && password.isNotBlank(),
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    if (loading) CircularProgressIndicator(modifier = Modifier.width(22.dp))
                    else Text("Entrar")
                }
            }
        }
    }
}
