package com.tonylex.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun SimpleFormDialog(
    title: String,
    fields: List<String>,
    onDismiss: () -> Unit,
    onSubmit: (List<String>) -> Unit,
) {
    var values by remember { mutableStateOf(List(fields.size) { "" }) }
    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            TextButton(onClick = { onSubmit(values) }) { Text("Guardar") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancelar") }
        },
        title = { Text(title) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                fields.forEachIndexed { index, label ->
                    OutlinedTextField(
                        value = values[index],
                        onValueChange = { next ->
                            values = values.toMutableList().also { it[index] = next }
                        },
                        label = { Text(label) },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp),
                        singleLine = true,
                    )
                }
            }
        },
        shape = RoundedCornerShape(20.dp),
    )
}
