package com.tonylex.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material.icons.filled.CloudSync
import androidx.compose.material.icons.filled.Folder
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.People
import androidx.compose.material.icons.filled.Router
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.tonylex.app.TonylexApp
import com.tonylex.app.data.sync.SyncWorker
import com.tonylex.app.ui.theme.TxDark
import com.tonylex.app.ui.theme.TxDark2
import com.tonylex.app.ui.theme.TxMuted
import com.tonylex.app.ui.theme.TxSoftBg
import com.tonylex.app.ui.theme.TxViolet
import com.tonylex.app.ui.theme.TxViolet2
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(onLogout: () -> Unit) {
    val app = LocalContext.current.applicationContext as TonylexApp
    val scope = rememberCoroutineScope()
    var tab by remember { mutableIntStateOf(0) }
    val pending by app.repository.outboxCount().collectAsState(initial = 0)
    var onlineHint by remember { mutableStateOf("Listo") }

    Scaffold(
        containerColor = TxSoftBg,
        topBar = {
            TopAppBar(
                title = {
                    Text("TONYLEX", fontWeight = FontWeight.ExtraBold)
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color.White,
                    titleContentColor = Color(0xFF1A1630),
                    actionIconContentColor = TxViolet,
                ),
                actions = {
                    if (pending > 0) {
                        Text("$pending pend.", color = TxViolet, modifier = Modifier.padding(end = 6.dp))
                    }
                    IconButton(onClick = {
                        scope.launch {
                            onlineHint = "Sincronizando…"
                            runCatching { app.repository.refresh() }
                                .onSuccess { onlineHint = "Sincronizado" }
                                .onFailure { onlineHint = it.message ?: "Sin red" }
                            SyncWorker.enqueue(app)
                        }
                    }) { Icon(Icons.Default.CloudSync, contentDescription = "Sync") }
                    IconButton(onClick = {
                        app.repository.logout()
                        onLogout()
                    }) { Icon(Icons.AutoMirrored.Filled.Logout, contentDescription = "Salir") }
                },
            )
        },
        bottomBar = {
            NavigationBar(containerColor = Color.White) {
                listOf(
                    Triple("Inicio", Icons.Default.Inventory2, 0),
                    Triple("Cajas", Icons.Default.Router, 1),
                    Triple("Clientes", Icons.Default.People, 2),
                    Triple("Mapa", Icons.Default.Map, 3),
                    Triple("Más", Icons.Default.Folder, 4),
                ).forEach { (label, icon, index) ->
                    NavigationBarItem(
                        selected = tab == index,
                        onClick = { tab = index },
                        icon = { Icon(icon, contentDescription = label) },
                        label = { Text(label) },
                    )
                }
            }
        },
    ) { padding ->
        Column(
            Modifier
                .fillMaxSize()
                .padding(padding)
                .background(TxSoftBg),
        ) {
            Text(
                onlineHint,
                color = TxViolet,
                style = MaterialTheme.typography.labelMedium,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            )
            when (tab) {
                0 -> DashboardTab()
                1 -> NatsTab()
                2 -> ClientesTab()
                3 -> MapTab()
                else -> MoreTab()
            }
        }
    }
}

@Composable
private fun DashboardTab() {
    val app = LocalContext.current.applicationContext as TonylexApp
    val nats by app.repository.nats().collectAsState(initial = emptyList())
    val clientes by app.repository.clientes().collectAsState(initial = emptyList())
    val potencias by app.repository.potencias().collectAsState(initial = emptyList())
    val activos = clientes.count { it.activo }

    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Text("Dashboard", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.ExtraBold)
            Text("Resumen offline de la red", color = TxMuted)
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                LightKpi("Cajas", nats.size.toString(), Modifier.weight(1f))
                LightKpi("Activos", activos.toString(), Modifier.weight(1f))
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                LightKpi("Clientes", clientes.size.toString(), Modifier.weight(1f))
                LightKpi("Potencias", potencias.size.toString(), Modifier.weight(1f))
            }
        }
        item {
            DarkPanel {
                Text("Actividad reciente", color = Color.White, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(10.dp))
                nats.take(6).forEachIndexed { idx, nat ->
                    DarkRow(
                        title = nat.nombre,
                        subtitle = nat.region ?: "Sin región",
                        trailing = "${nat.puertosTotal} p",
                        active = idx == 0,
                    )
                }
            }
        }
    }
}

@Composable
private fun LightKpi(title: String, value: String, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier.height(110.dp),
        shape = RoundedCornerShape(22.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Box(Modifier.fillMaxSize().padding(16.dp)) {
            Column {
                Text(title, color = TxMuted, style = MaterialTheme.typography.labelLarge)
                Text(value, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.ExtraBold)
            }
            Box(
                Modifier
                    .align(Alignment.BottomEnd)
                    .size(48.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .background(Brush.linearGradient(listOf(Color(0x337C3AED), Color(0x14A78BFA)))),
            )
        }
    }
}

@Composable
private fun DarkPanel(content: @Composable () -> Unit) {
    Card(
        shape = RoundedCornerShape(26.dp),
        colors = CardDefaults.cardColors(containerColor = TxDark),
        elevation = CardDefaults.cardElevation(defaultElevation = 6.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            Modifier
                .background(Brush.verticalGradient(listOf(TxDark, TxDark2)))
                .padding(16.dp),
        ) { content() }
    }
}

@Composable
private fun DarkRow(title: String, subtitle: String, trailing: String, active: Boolean) {
    Row(
        Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp)
            .clip(RoundedCornerShape(16.dp))
            .background(
                if (active) Brush.linearGradient(listOf(TxViolet, TxViolet2))
                else Brush.linearGradient(listOf(Color.Transparent, Color.Transparent)),
            )
            .padding(12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Box(
                Modifier
                    .size(36.dp)
                    .clip(CircleShape)
                    .background(Color.White.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center,
            ) {
                Text(title.take(1), color = Color.White, fontWeight = FontWeight.Bold)
            }
            Column {
                Text(title, color = Color.White, fontWeight = FontWeight.SemiBold)
                Text(subtitle, color = Color.White.copy(alpha = 0.7f), style = MaterialTheme.typography.bodySmall)
            }
        }
        Text(trailing, color = Color.White, fontWeight = FontWeight.Bold)
    }
}

@Composable
fun NatsTab() {
    val app = LocalContext.current.applicationContext as TonylexApp
    val items by app.repository.nats().collectAsState(initial = emptyList())
    var showAdd by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Column(Modifier.padding(horizontal = 16.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Column {
                Text("Cajas NAP", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                Text("Consulta y CRUD offline", color = TxMuted)
            }
            FloatingActionButton(
                onClick = { showAdd = true },
                shape = CircleShape,
                containerColor = TxViolet,
                contentColor = Color.White,
            ) { Text("+", fontWeight = FontWeight.Bold) }
        }
        Spacer(Modifier.height(12.dp))
        DarkPanel {
            items.forEachIndexed { idx, nat ->
                DarkRow(
                    title = nat.nombre,
                    subtitle = listOfNotNull(nat.region, if (nat.localOnly) "Pendiente sync" else null).joinToString(" · "),
                    trailing = "${nat.puertosTotal}",
                    active = idx == 0,
                )
            }
        }
    }

    if (showAdd) {
        SimpleFormDialog(
            title = "Nueva caja",
            fields = listOf("Nombre", "Región", "Puertos"),
            onDismiss = { showAdd = false },
            onSubmit = { values ->
                scope.launch {
                    app.repository.saveNatLocal(
                        nombre = values[0],
                        region = values[1].ifBlank { null },
                        puertos = values[2].toIntOrNull() ?: 8,
                        lat = null,
                        lon = null,
                    )
                    showAdd = false
                }
            },
        )
    }
}

@Composable
fun ClientesTab() {
    val app = LocalContext.current.applicationContext as TonylexApp
    val items by app.repository.clientes().collectAsState(initial = emptyList())
    val nats by app.repository.nats().collectAsState(initial = emptyList())
    var showAdd by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Column(Modifier.padding(horizontal = 16.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Column {
                Text("Clientes", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                Text("Listado con sync diferido", color = TxMuted)
            }
            FloatingActionButton(
                onClick = { showAdd = true },
                shape = CircleShape,
                containerColor = TxViolet,
                contentColor = Color.White,
            ) { Text("+", fontWeight = FontWeight.Bold) }
        }
        Spacer(Modifier.height(12.dp))
        DarkPanel {
            items.forEachIndexed { idx, c ->
                DarkRow(
                    title = c.nombre,
                    subtitle = c.direccion,
                    trailing = if (c.activo) "OK" else "Off",
                    active = idx == 0,
                )
            }
        }
    }

    if (showAdd) {
        SimpleFormDialog(
            title = "Nuevo cliente",
            fields = listOf("Nombre", "Dirección", "NAT id", "Plan", "Contacto"),
            onDismiss = { showAdd = false },
            onSubmit = { values ->
                val natId = values[2].toIntOrNull() ?: nats.firstOrNull()?.id ?: return@SimpleFormDialog
                scope.launch {
                    app.repository.saveClienteLocal(
                        nombre = values[0],
                        direccion = values[1],
                        natId = natId,
                        plan = values[3].ifBlank { null },
                        contacto = values[4].ifBlank { null },
                    )
                    showAdd = false
                }
            },
        )
    }
}

@Composable
fun MoreTab() {
    LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Card(shape = RoundedCornerShape(22.dp), colors = CardDefaults.cardColors(Color.White), modifier = Modifier.fillMaxWidth()) {
                PotenciasInline()
            }
        }
        item {
            Card(shape = RoundedCornerShape(22.dp), colors = CardDefaults.cardColors(Color.White), modifier = Modifier.fillMaxWidth()) {
                AsistenciasInline()
            }
        }
        item {
            Card(shape = RoundedCornerShape(22.dp), colors = CardDefaults.cardColors(Color.White), modifier = Modifier.fillMaxWidth()) {
                DocumentosInline()
            }
        }
    }
}

@Composable
private fun PotenciasInline() {
    val app = LocalContext.current.applicationContext as TonylexApp
    val items by app.repository.potencias().collectAsState(initial = emptyList())
    var showAdd by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    Column(Modifier.padding(16.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Potencias", fontWeight = FontWeight.Bold)
            FloatingActionButton(onClick = { showAdd = true }, shape = CircleShape, containerColor = TxViolet, contentColor = Color.White, modifier = Modifier.size(40.dp)) {
                Text("+")
            }
        }
        items.take(20).forEach { p ->
            Text("#${p.id} CLI ${p.clienteId}: ${p.potenciaEntrada}/${p.potenciaSalida} dBm", color = TxMuted)
        }
    }
    if (showAdd) {
        SimpleFormDialog(
            title = "Nueva potencia",
            fields = listOf("Cliente id", "NAP id", "Entrada", "Salida", "Técnico"),
            onDismiss = { showAdd = false },
            onSubmit = { v ->
                scope.launch {
                    app.repository.savePotenciaLocal(
                        clienteId = v[0].toInt(),
                        napId = v[1].toIntOrNull(),
                        entrada = v[2].toDouble(),
                        salida = v[3].toDouble(),
                        tecnico = v[4].ifBlank { null },
                    )
                    showAdd = false
                }
            },
        )
    }
}

@Composable
private fun AsistenciasInline() {
    val app = LocalContext.current.applicationContext as TonylexApp
    val items by app.repository.asistencias().collectAsState(initial = emptyList())
    val trabajadores by app.repository.trabajadores().collectAsState(initial = emptyList())
    var showAdd by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    Column(Modifier.padding(16.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Asistencias", fontWeight = FontWeight.Bold)
            FloatingActionButton(onClick = { showAdd = true }, shape = CircleShape, containerColor = TxViolet, contentColor = Color.White, modifier = Modifier.size(40.dp)) {
                Text("+")
            }
        }
        items.take(20).forEach { a ->
            Text("Trab ${a.trabajadorId}: ${a.tipo} ${a.fechaHora ?: ""}", color = TxMuted)
        }
    }
    if (showAdd) {
        SimpleFormDialog(
            title = "Registrar asistencia",
            fields = listOf("Trabajador id", "Tipo (entrada/salida)"),
            onDismiss = { showAdd = false },
            onSubmit = { v ->
                scope.launch {
                    val tid = v[0].toIntOrNull() ?: trabajadores.firstOrNull()?.id ?: return@launch
                    app.repository.saveAsistenciaLocal(tid, v[1].ifBlank { "entrada" })
                    showAdd = false
                }
            },
        )
    }
}

@Composable
private fun DocumentosInline() {
    val app = LocalContext.current.applicationContext as TonylexApp
    val items by app.repository.documentos().collectAsState(initial = emptyList())
    Column(Modifier.padding(16.dp)) {
        Text("Documentos", fontWeight = FontWeight.Bold)
        items.take(30).forEach { d ->
            Text("${d.nombreOriginal ?: d.nombre}", color = TxMuted)
        }
    }
}
