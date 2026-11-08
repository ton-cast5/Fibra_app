package com.tonylex.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.CloudSync
import androidx.compose.material.icons.filled.Folder
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.People
import androidx.compose.material.icons.filled.Router
import androidx.compose.material.icons.filled.Tune
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
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
import androidx.compose.ui.unit.sp
import com.tonylex.app.TonylexApp
import com.tonylex.app.data.local.NapModelEntity
import com.tonylex.app.data.local.NatEntity
import com.tonylex.app.data.sync.SyncWorker
import com.tonylex.app.ui.theme.TxDark
import com.tonylex.app.ui.theme.TxDark2
import com.tonylex.app.ui.theme.TxMuted
import com.tonylex.app.ui.theme.TxSoftBg
import com.tonylex.app.ui.theme.TxViolet
import com.tonylex.app.ui.theme.TxViolet2
import kotlinx.coroutines.launch

private val FnBg = Color(0xFFECEAF3)
private val FnInk = Color(0xFF14131C)
private val FnViolet = Color(0xFF6C5CEF)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(onLogout: () -> Unit) {
    val app = LocalContext.current.applicationContext as TonylexApp
    val scope = rememberCoroutineScope()
    var tab by remember { mutableIntStateOf(0) }
    val pending by app.repository.outboxCount().collectAsState(initial = 0)
    var hint by remember { mutableStateOf("Listo") }

    Scaffold(
        containerColor = FnBg,
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("TONYLEX", fontWeight = FontWeight.ExtraBold, color = FnInk, fontSize = 18.sp)
                        Text("Red óptica, mejor operación", color = TxMuted, fontSize = 11.sp)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.White),
                actions = {
                    if (pending > 0) Text("$pending", color = FnViolet, modifier = Modifier.padding(end = 4.dp))
                    IconButton(onClick = {
                        scope.launch {
                            hint = "Sincronizando…"
                            runCatching { app.repository.refresh() }
                                .onSuccess { hint = "Sincronizado" }
                                .onFailure { hint = it.message ?: "Sin red" }
                            SyncWorker.enqueue(app)
                        }
                    }) { Icon(Icons.Default.CloudSync, null, tint = FnViolet) }
                    IconButton(onClick = {
                        app.repository.logout()
                        onLogout()
                    }) { Icon(Icons.AutoMirrored.Filled.Logout, null, tint = FnInk) }
                },
            )
        },
        bottomBar = {
            NavigationBar(containerColor = TxDark, contentColor = Color.White) {
                listOf(
                    Triple("Resumen", Icons.Default.Inventory2, 0),
                    Triple("Cajas", Icons.Default.Router, 1),
                    Triple("Clientes", Icons.Default.People, 2),
                    Triple("Mapa", Icons.Default.Map, 3),
                    Triple("Módulos", Icons.Default.Folder, 4),
                ).forEach { (label, icon, index) ->
                    NavigationBarItem(
                        selected = tab == index,
                        onClick = { tab = index },
                        icon = { Icon(icon, label) },
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
                .background(FnBg),
        ) {
            Text(hint, color = FnViolet, fontSize = 12.sp, modifier = Modifier.padding(horizontal = 16.dp, vertical = 6.dp))
            when (tab) {
                0 -> FinnovaDashboard()
                1 -> NatsTab()
                2 -> ClientesTab()
                3 -> MapTab()
                else -> ModulesHub(onOpen = { tab = it })
            }
        }
    }
}

@Composable
private fun FinnovaDashboard() {
    val app = LocalContext.current.applicationContext as TonylexApp
    val nats by app.repository.nats().collectAsState(initial = emptyList())
    val clientes by app.repository.clientes().collectAsState(initial = emptyList())
    val potencias by app.repository.potencias().collectAsState(initial = emptyList())
    var selected by remember { mutableIntStateOf(0) }
    val activos = clientes.count { it.activo }
    val scope = rememberCoroutineScope()
    var showAdd by remember { mutableStateOf(false) }
    var query by remember { mutableStateOf("") }
    val suggestions = remember(query, nats, clientes) {
        val q = query.trim().lowercase()
        if (q.isEmpty()) emptyList()
        else {
            val cajaHits = nats.filter {
                it.nombre.lowercase().contains(q) || (it.region ?: "").lowercase().contains(q)
            }.take(5).map { "Caja · ${it.nombre}" }
            val cliHits = clientes.filter {
                it.nombre.lowercase().contains(q) || it.direccion.lowercase().contains(q)
            }.take(5).map { "Cliente · ${it.nombre}" }
            cajaHits + cliHits
        }
    }

    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Column {
                        Text("Resumen", fontWeight = FontWeight.ExtraBold, fontSize = 24.sp, color = FnInk)
                        Text("Vista clara del estado de tu red.", color = TxMuted, fontSize = 13.sp)
                }
                Button(
                    onClick = { showAdd = true },
                    shape = RoundedCornerShape(999.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = FnViolet),
                ) {
                    Icon(Icons.Default.Add, null)
                    Text(" Crear caja")
                }
            }
        }

        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                KpiCard("Activos", activos.toString(), "En línea", Modifier.weight(1f))
                KpiCard("Cajas", nats.size.toString(), "Red", Modifier.weight(1f))
            }
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                KpiCard("Clientes", clientes.size.toString(), "Total", Modifier.weight(1f))
                KpiCard("Potencias", potencias.size.toString(), "Mediciones", Modifier.weight(1f))
            }
        }

        item {
            OutlinedTextField(
                value = query,
                onValueChange = { query = it },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                placeholder = { Text("Buscar cliente o caja…") },
                shape = RoundedCornerShape(999.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedContainerColor = Color.White,
                    unfocusedContainerColor = Color.White,
                    focusedBorderColor = FnViolet,
                    unfocusedBorderColor = Color(0x14000000),
                ),
            )
        }
        if (suggestions.isNotEmpty()) {
            item {
                Card(shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(Color.White), modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        suggestions.forEach {
                            Text(it, color = FnInk, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(vertical = 4.dp, horizontal = 6.dp))
                        }
                    }
                }
            }
        }

        item {
            DarkWorkspace(
                nats = nats,
                selected = selected,
                onSelect = { selected = it },
                clientesActivos = activos,
                totalClientes = clientes.size,
            )
        }
    }

    if (showAdd) {
        SimpleFormDialog(
            title = "Nueva caja",
            fields = listOf("Nombre", "Región", "Puertos"),
            onDismiss = { showAdd = false },
            onSubmit = { values ->
                scope.launch {
                    app.repository.saveNatLocal(values[0], values[1].ifBlank { null }, values[2].toIntOrNull() ?: 8, null, null)
                    showAdd = false
                }
            },
        )
    }
}

@Composable
private fun FilterChip(text: String) {
    Text(
        text,
        modifier = Modifier
            .clip(RoundedCornerShape(999.dp))
            .background(Color.White)
            .border(1.dp, Color(0x14000000), RoundedCornerShape(999.dp))
            .padding(horizontal = 12.dp, vertical = 8.dp),
        fontSize = 12.sp,
        fontWeight = FontWeight.SemiBold,
        color = FnInk,
    )
}

@Composable
private fun KpiCard(label: String, value: String, hint: String, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier.height(120.dp),
        shape = RoundedCornerShape(22.dp),
        colors = CardDefaults.cardColors(Color.White),
        elevation = CardDefaults.cardElevation(2.dp),
    ) {
        Box(Modifier.fillMaxSize().padding(14.dp)) {
            Column {
                Text(label, color = TxMuted, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                Text(value, fontWeight = FontWeight.ExtraBold, fontSize = 28.sp, color = FnInk)
                Text(hint, color = FnViolet, fontSize = 12.sp, fontWeight = FontWeight.Bold)
            }
            Row(
                Modifier.align(Alignment.BottomEnd),
                horizontalArrangement = Arrangement.spacedBy(3.dp),
                verticalAlignment = Alignment.Bottom,
            ) {
                listOf(0.4f, 0.7f, 0.55f, 0.85f, 0.6f).forEach {
                    Box(
                        Modifier
                            .width(8.dp)
                            .height((36 * it).dp)
                            .clip(RoundedCornerShape(4.dp))
                            .background(Brush.verticalGradient(listOf(Color(0xFFA78BFA), FnViolet))),
                    )
                }
            }
        }
    }
}

@Composable
private fun DarkWorkspace(
    nats: List<NatEntity>,
    selected: Int,
    onSelect: (Int) -> Unit,
    clientesActivos: Int,
    totalClientes: Int,
) {
    val current = nats.getOrNull(selected)
    val panelBg = Color(0xFFF7F5FC)
    Card(
        shape = RoundedCornerShape(30.dp),
        colors = CardDefaults.cardColors(Color.White),
        elevation = CardDefaults.cardElevation(4.dp),
        modifier = Modifier.fillMaxWidth().height(460.dp),
    ) {
        Row(Modifier.fillMaxSize().background(panelBg)) {
            Column(
                Modifier
                    .width(160.dp)
                    .fillMaxHeight()
                    .background(Color.White.copy(alpha = 0.7f))
                    .padding(12.dp),
            ) {
                Text("Cajas", color = FnInk, fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 8.dp))
                LazyColumn(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    itemsIndexed(nats.take(20)) { idx, nat ->
                        val active = idx == selected
                        Row(
                            Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(16.dp))
                                .then(
                                    if (active) Modifier.background(Brush.linearGradient(listOf(FnViolet, TxViolet2)))
                                    else Modifier.background(Color.Transparent),
                                )
                                .clickable { onSelect(idx) }
                                .padding(10.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Box(
                                Modifier.size(32.dp).clip(CircleShape).background(
                                    if (active) Color.White.copy(0.2f) else Color(0xFFEEEAFB),
                                ),
                                contentAlignment = Alignment.Center,
                            ) {
                                Text(
                                    nat.nombre.take(1),
                                    color = if (active) Color.White else FnViolet,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp,
                                )
                            }
                            Spacer(Modifier.width(8.dp))
                            Column {
                                Text(
                                    nat.nombre,
                                    color = if (active) Color.White else FnInk,
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    maxLines = 1,
                                )
                                Text(
                                    "${nat.puertosTotal} p",
                                    color = if (active) Color.White.copy(0.75f) else TxMuted,
                                    fontSize = 10.sp,
                                )
                            }
                        }
                    }
                }
            }

            Column(
                Modifier
                    .weight(1f)
                    .fillMaxHeight()
                    .padding(14.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Text("Panel de operación", color = TxMuted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                Text(
                    if (current != null) "# ${current.nombre}" else "TONYLEX",
                    color = FnInk,
                    fontWeight = FontWeight.ExtraBold,
                    fontSize = 20.sp,
                )
                Text(
                    current?.region ?: "Tu red está al día — todo claro a simple vista",
                    color = TxMuted,
                    fontSize = 12.sp,
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    SoftStat("Puertos", "${current?.puertosTotal ?: nats.sumOf { it.puertosTotal }}")
                    SoftStat("Activos", "$clientesActivos")
                    SoftStat("Total", "$totalClientes")
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Box(
                        Modifier
                            .weight(1f)
                            .height(48.dp)
                            .clip(RoundedCornerShape(16.dp))
                            .background(FnViolet.copy(alpha = 0.12f))
                            .border(1.dp, FnViolet.copy(alpha = 0.28f), RoundedCornerShape(16.dp)),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text("+ Agregar", color = FnViolet, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    }
                    Box(
                        Modifier
                            .weight(1f)
                            .height(48.dp)
                            .clip(RoundedCornerShape(16.dp))
                            .background(Color.White)
                            .border(1.dp, Color(0x14000000), RoundedCornerShape(16.dp)),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text("Ver cajas", color = FnInk, fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
                    }
                }
                Spacer(Modifier.weight(1f))
                Row(
                    Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(18.dp))
                        .background(Color.White)
                        .border(1.dp, Color(0x14000000), RoundedCornerShape(18.dp))
                        .padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column {
                        Text("Balance red", color = TxMuted, fontSize = 11.sp)
                        Text("${nats.size} cajas", color = FnInk, fontWeight = FontWeight.Bold)
                    }
                    Box(
                        Modifier
                            .clip(RoundedCornerShape(999.dp))
                            .background(FnViolet)
                            .padding(horizontal = 14.dp, vertical = 8.dp),
                    ) {
                        Text("Ver detalle", color = Color.White, fontWeight = FontWeight.ExtraBold, fontSize = 12.sp)
                    }
                }
            }
        }
    }
}

@Composable
private fun SoftStat(label: String, value: String) {
    Column(
        Modifier
            .clip(RoundedCornerShape(16.dp))
            .background(Color.White)
            .border(1.dp, Color(0x14000000), RoundedCornerShape(16.dp))
            .padding(10.dp)
            .width(72.dp),
    ) {
        Text(label, color = TxMuted, fontSize = 10.sp)
        Text(value, color = FnInk, fontWeight = FontWeight.ExtraBold, fontSize = 16.sp)
    }
}

@Composable
fun NatsTab() {
    val app = LocalContext.current.applicationContext as TonylexApp
    val items by app.repository.nats().collectAsState(initial = emptyList())
    var showAdd by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    Column(Modifier.padding(16.dp)) {
        PageHead("Cajas", "Gestiona NAP y empalmes offline") {
            showAdd = true
        }
        Spacer(Modifier.height(12.dp))
        DarkWorkspace(items, 0, {}, 0, items.size)
    }
    if (showAdd) {
        SimpleFormDialog("Nueva caja", listOf("Nombre", "Región", "Puertos"), { showAdd = false }) { v ->
            scope.launch {
                app.repository.saveNatLocal(v[0], v[1].ifBlank { null }, v[2].toIntOrNull() ?: 8, null, null)
                showAdd = false
            }
        }
    }
}

@Composable
fun ClientesTab() {
    val app = LocalContext.current.applicationContext as TonylexApp
    val items by app.repository.clientes().collectAsState(initial = emptyList())
    val nats by app.repository.nats().collectAsState(initial = emptyList())
    var showAdd by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    Column(Modifier.padding(16.dp)) {
        PageHead("Clientes", "Administra clientes con sync diferido") { showAdd = true }
        Spacer(Modifier.height(12.dp))
        Card(shape = RoundedCornerShape(28.dp), colors = CardDefaults.cardColors(TxDark), modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                items.take(30).forEachIndexed { idx, c ->
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(16.dp))
                            .background(if (idx == 0) FnViolet else Color.Transparent)
                            .padding(12.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Column {
                            Text(c.nombre, color = Color.White, fontWeight = FontWeight.SemiBold)
                            Text(c.direccion, color = Color.White.copy(0.7f), fontSize = 12.sp)
                        }
                        Text(if (c.activo) "OK" else "Off", color = Color.White, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
    if (showAdd) {
        SimpleFormDialog("Nuevo cliente", listOf("Nombre", "Dirección", "NAT id", "Plan", "Contacto"), { showAdd = false }) { v ->
            val natId = v[2].toIntOrNull() ?: nats.firstOrNull()?.id ?: return@SimpleFormDialog
            scope.launch {
                app.repository.saveClienteLocal(v[0], v[1], natId, v[3].ifBlank { null }, v[4].ifBlank { null })
                showAdd = false
            }
        }
    }
}

@Composable
private fun PageHead(title: String, subtitle: String, onAdd: () -> Unit) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
        Column {
            Text(title, fontWeight = FontWeight.ExtraBold, fontSize = 24.sp, color = FnInk)
            Text(subtitle, color = TxMuted, fontSize = 13.sp)
        }
        FloatingActionButton(onClick = onAdd, shape = CircleShape, containerColor = FnViolet, contentColor = Color.White) {
            Icon(Icons.Default.Add, null)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ModulesHub(onOpen: (Int) -> Unit) {
    val app = LocalContext.current.applicationContext as TonylexApp
    val potencias by app.repository.potencias().collectAsState(initial = emptyList())
    val asistencias by app.repository.asistencias().collectAsState(initial = emptyList())
    val docs by app.repository.documentos().collectAsState(initial = emptyList())
    val nats by app.repository.nats().collectAsState(initial = emptyList())
    val clientes by app.repository.clientes().collectAsState(initial = emptyList())
    val modelos by app.repository.napModels().collectAsState(initial = emptyList())
    var modelQuery by remember { mutableStateOf("") }
    val filteredModels = remember(modelQuery, modelos) {
        val q = modelQuery.trim().lowercase()
        if (q.isEmpty()) modelos else modelos.filter {
            it.nombre.lowercase().contains(q) || (it.tipoCaja ?: "").lowercase().contains(q)
        }
    }

    LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text("Todos los módulos", fontWeight = FontWeight.ExtraBold, fontSize = 24.sp, color = FnInk)
            Text("Misma experiencia clara que en web", color = TxMuted, fontSize = 13.sp)
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                ModuleTile("Resumen", "Inicio", Modifier.weight(1f)) { onOpen(0) }
                ModuleTile("Cajas", "${nats.size}", Modifier.weight(1f)) { onOpen(1) }
            }
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                ModuleTile("Clientes", "${clientes.size}", Modifier.weight(1f)) { onOpen(2) }
                ModuleTile("Mapa", "OSM", Modifier.weight(1f)) { onOpen(3) }
            }
        }
        item {
            Text("Catálogo de modelos", fontWeight = FontWeight.ExtraBold, fontSize = 18.sp, color = FnInk)
            Text("${modelos.size} referencias visuales", color = TxMuted, fontSize = 12.sp)
        }
        item {
            OutlinedTextField(
                value = modelQuery,
                onValueChange = { modelQuery = it },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                placeholder = { Text("Filtrar modelos…") },
                shape = RoundedCornerShape(18.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedContainerColor = Color.White,
                    unfocusedContainerColor = Color.White,
                    focusedBorderColor = FnViolet,
                    unfocusedBorderColor = Color(0x14000000),
                ),
            )
        }
        items(filteredModels.chunked(2)) { row ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                row.forEach { model ->
                    ModelCatalogCard(model, Modifier.weight(1f))
                }
                if (row.size == 1) Spacer(Modifier.weight(1f))
            }
        }
        item {
            Card(shape = RoundedCornerShape(22.dp), colors = CardDefaults.cardColors(Color.White), modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Potencias · ${potencias.size}", fontWeight = FontWeight.Bold, color = FnInk)
                    potencias.take(6).forEach {
                        Text("#${it.id}  ${it.potenciaEntrada}/${it.potenciaSalida} dBm", color = TxMuted, fontSize = 12.sp)
                    }
                    Text("Asistencias · ${asistencias.size}", fontWeight = FontWeight.Bold, color = FnInk)
                    Text("Documentos · ${docs.size}", fontWeight = FontWeight.Bold, color = FnInk)
                }
            }
        }
    }
}

@Composable
private fun ModelCatalogCard(model: NapModelEntity, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier.height(150.dp),
        shape = RoundedCornerShape(22.dp),
        colors = CardDefaults.cardColors(Color.White),
        elevation = CardDefaults.cardElevation(2.dp),
    ) {
        Column(Modifier.fillMaxSize()) {
            Box(
                Modifier
                    .fillMaxWidth()
                    .height(72.dp)
                    .background(Brush.linearGradient(listOf(Color(0xFFF4F2FA), Color(0xFFE9E6F5)))),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    if (model.tipoCaja == "empalme") "Empalme" else "NAP",
                    color = FnViolet,
                    fontWeight = FontWeight.ExtraBold,
                )
            }
            Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(model.nombre, fontWeight = FontWeight.Bold, color = FnInk, maxLines = 1, fontSize = 13.sp)
                Text(
                    model.capacidadMax?.let { "$it puertos" } ?: "Sin límite",
                    color = TxMuted,
                    fontSize = 12.sp,
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ModuleTile(title: String, subtitle: String, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Card(
        onClick = onClick,
        modifier = modifier.height(96.dp),
        shape = RoundedCornerShape(22.dp),
        colors = CardDefaults.cardColors(Color.White),
        elevation = CardDefaults.cardElevation(2.dp),
    ) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.SpaceBetween) {
            Text(title, fontWeight = FontWeight.ExtraBold, color = FnInk)
            Text(subtitle, color = FnViolet, fontWeight = FontWeight.Bold, fontSize = 13.sp)
        }
    }
}
