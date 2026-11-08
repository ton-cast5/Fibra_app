package com.tonylex.app.ui.screens

import android.view.ViewGroup
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.tonylex.app.TonylexApp
import org.osmdroid.config.Configuration
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker

@Composable
fun MapTab() {
    val app = LocalContext.current.applicationContext as TonylexApp
    val nats by app.repository.nats().collectAsState(initial = emptyList())
    AndroidView(
        modifier = Modifier
            .fillMaxSize()
            .padding(8.dp),
        factory = { context ->
            Configuration.getInstance().userAgentValue = context.packageName
            MapView(context).apply {
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT,
                )
                setTileSource(TileSourceFactory.MAPNIK)
                setMultiTouchControls(true)
                controller.setZoom(13.0)
                controller.setCenter(GeoPoint(19.4326, -99.1332))
            }
        },
        update = { map ->
            map.overlays.removeAll { it is Marker }
            var first: GeoPoint? = null
            nats.forEach { nat ->
                val lat = nat.latitud ?: return@forEach
                val lon = nat.longitud ?: return@forEach
                val point = GeoPoint(lat, lon)
                if (first == null) first = point
                map.overlays.add(
                    Marker(map).apply {
                        position = point
                        title = nat.nombre
                        snippet = nat.region ?: ""
                        setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
                    },
                )
            }
            first?.let { map.controller.setCenter(it) }
            map.invalidate()
        },
    )
}
