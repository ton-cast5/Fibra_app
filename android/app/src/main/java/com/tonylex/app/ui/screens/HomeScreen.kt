package com.tonylex.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material.icons.filled.CloudSync
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.People
import androidx.compose.material.icons.filled.Router
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.EventAvailable
import androidx.compose.material.icons.filled.Folder
import androidx.compose.material.icons.filled.Inventory2
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.tonylex.app.TonylexApp
import com.tonylex.app.data.sync.SyncWorker
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(onLogout: () -> Unit) {
    val app = LocalContext.current.applicationContext as TonylexApp
    val scope = rememberCoroutineScope()
    var tab by remember { mutableIntStateOf(0) }
    val pending by app.repository.outboxCount().collectAsState(initial = 0)
    var onlineHint by remember { mutableStateOf("Sync listo") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("TONYLEX") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    actionIconContentColor = MaterialTheme.colorScheme.onPrimary,
                ),
                actions = {
                    if (pending > 0) {
                        Text("$pending pend.", modifier = Modifier.padding(end = 8.dp))
                    }
                    IconButton(onClick = {
                        scope.launch {
                            onlineHint = "Sincronizando…"
                            runCatching { app.repository.refresh() }
                                .onSuccess { onlineHint = "Sincronizado" }
                                .onFailure { onlineHint = it.message ?: "Sin red" }
                            SyncWorker.enqueue(app)
                        }
                    }) {
                        Icon(Icons.Default.CloudSync, contentDescription = "Sync")
                    }
                    IconButton(onClick = {
                        app.repository.logout()
                        onLogout()
                    }) {
                        Icon(Icons.AutoMirrored.Filled.Logout, contentDescription = "Salir")
                    }
                },
            )
        },
        bottomBar = {
            NavigationBar {
                val items = listOf(
                    Triple("Inicio", Icons.Default.Inventory2, 0),
                    Triple("Cajas", Icons.Default.Router, 1),
                    Triple("Clientes", Icons.Default.People, 2),
                    Triple("Mapa", Icons.Default.Map, 3),
                    Triple("Más", Icons.Default.Folder, 4),
                )
                items.forEach { (label, icon, index) ->
                    NavigationBarItem(
                        selected = tab == index,
                        onClick = { tab = index },
                        icon = { Icon(icon, contentDescription = label) },
                        label = { Text(label) },
                    )
                }
            }
        },
        floatingActionButton = {
            if (tab in 1..2) {
                FloatingActionButton(
                    onClick = { /* handled in child via dialogs */ },
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Text("+")
                }
            }
        },
    ) { padding ->
        Column(
            Modifier
                .fillMaxSize()
                .padding(padding),
        ) {
            Text(
                onlineHint,
                style = MaterialTheme.typography.labelMedium,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 6.dp),
                color = MaterialTheme.colorScheme.primary,
            )
            when (tab) {
                0 -> DashboardTab()
                1 -> NatsTab()
                2 -> ClientesTab()
                3 -> MapTab()
                else -> MoreTab(onSelect = { tab = it })
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
            Text("Resumen offline", style = MaterialTheme.typography.titleLarge)
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                StatCard("Cajas", nats.size.toString(), Modifier.weight(1f))
                StatCard("Activos", activos.toString(), Modifier.weight(1f))
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                StatCard("Clientes", clientes.size.toString(), Modifier.weight(1f))
                StatCard("Potencias", potencias.size.toString(), Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun StatCard(title: String, value: String, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primary),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text(title, color = MaterialTheme.colorScheme.onPrimary)
            Text(value, style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.onPrimary)
        }
    }
}

@Composable
fun NatsTab() {
    val app = LocalContext.current.applicationContext as TonylexApp
    val items by app.repository.nats().collectAsState(initial = emptyList())
    var showAdd by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Column {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Cajas NAP", style = MaterialTheme.typography.titleMedium)
            FloatingActionButton(onClick = { showAdd = true }, shape = RoundedCornerShape(14.dp)) {
                Text("+")
            }
        }
        LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(items, key = { it.id }) { nat ->
                Card(shape = RoundedCornerShape(16.dp), modifier = Modifier.fillMaxWidth()) {
                    Row(
                        Modifier.padding(14.dp).fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Column {
                            Text(nat.nombre, style = MaterialTheme.typography.titleMedium)
                            Text("${nat.region ?: "—"} · ${nat.puertosTotal} puertos")
                            if (nat.localOnly) Text("Pendiente de sync", color = MaterialTheme.colorScheme.primary)
                        }
                        IconButton(onClick = {
                            scope.launch { app.repository.deleteNat(nat.id) }
                        }) { Text("✕") }
                    }
                }
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

    Column {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Clientes", style = MaterialTheme.typography.titleMedium)
            FloatingActionButton(onClick = { showAdd = true }, shape = RoundedCornerShape(14.dp)) {
                Text("+")
            }
        }
        LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(items, key = { it.id }) { c ->
                Card(shape = RoundedCornerShape(16.dp), modifier = Modifier.fillMaxWidth()) {
                    Row(
                        Modifier.padding(14.dp).fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Column {
                            Text(c.nombre, style = MaterialTheme.typography.titleMedium)
                            Text(c.direccion)
                            Text(if (c.activo) "Activo" else "Inactivo")
                        }
                        IconButton(onClick = {
                            scope.launch { app.repository.deleteCliente(c.id) }
                        }) { Text("✕") }
                    }
                }
            }
        }
    }

    if (showAdd) {
        SimpleFormDialog(
            title = "Nuevo cliente",
            fields = listOf("Nombre", "Dirección", "NAT id", "Plan", "Contacto"),
            onDismiss = { showAdd = false },
            onSubmit = { values ->
                val natId = values[2].toIntOrNull() ?: nats.firstOrNull()?.id
                if (natId == null) return@SimpleFormDialog
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
fun MoreTab(onSelect: (Int) -> Unit) {
    LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item {
            Card(shape = RoundedCornerShape(16.dp), modifier = Modifier.fillMaxWidth()) {
                PotenciasInline()
            }
        }
        item {
            Card(shape = RoundedCornerShape(16.dp), modifier = Modifier.fillMaxWidth()) {
                AsistenciasInline()
            }
        }
        item {
            Card(shape = RoundedCornerShape(16.dp), modifier = Modifier.fillMaxWidth()) {
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
    Column(Modifier.padding(14.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Potencias", style = MaterialTheme.typography.titleMedium)
            FloatingActionButton(onClick = { showAdd = true }, shape = RoundedCornerShape(12.dp)) { Text("+") }
        }
        items.take(20).forEach { p ->
            Text("#${p.id} CLI ${p.clienteId}: ${p.potenciaEntrada}/${p.potenciaSalida} dBm (${p.estado})")
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
    Column(Modifier.padding(14.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Asistencias", style = MaterialTheme.typography.titleMedium)
            FloatingActionButton(onClick = { showAdd = true }, shape = RoundedCornerShape(12.dp)) { Text("+") }
        }
        items.take(20).forEach { a ->
            Text("Trab ${a.trabajadorId}: ${a.tipo} ${a.fechaHora ?: ""}")
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
    Column(Modifier.padding(14.dp)) {
        Text("Documentos (metadatos)", style = MaterialTheme.typography.titleMedium)
        items.take(30).forEach { d ->
            Text("${d.nombreOriginal ?: d.nombre} (${d.extension})")
        }
    }
}
