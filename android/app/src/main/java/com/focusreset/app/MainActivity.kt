package com.focusreset.app

import android.app.Activity
import android.app.AppOpsManager
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.*
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.Executors
import org.json.JSONArray
import org.json.JSONObject

class MainActivity : Activity() {
    private val executor = Executors.newSingleThreadExecutor()
    private lateinit var api: EditText
    private lateinit var token: EditText
    private lateinit var status: TextView
    private lateinit var preview: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val prefs = getPreferences(MODE_PRIVATE)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(28, 30, 28, 24)
            setBackgroundColor(0xFFF5F7F6.toInt())
        }
        root.addView(TextView(this).apply { text="Focus Reset"; textSize=28f; setTextColor(0xFF17221E.toInt()) })
        root.addView(TextView(this).apply { text="30-day screen-time companion"; textSize=14f; setTextColor(0xFF748078.toInt()) })
        api = EditText(this).apply { hint="Backend URL e.g. http://192.168.1.10:8000"; setSingleLine(); setText(prefs.getString("api","http://192.168.1.10:8000")) }
        root.addView(api)
        token = EditText(this).apply { hint="API token from web dashboard"; setSingleLine(); setText(prefs.getString("token","")) }
        root.addView(token)
        root.addView(button("Grant Usage Access") { startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)) })
        root.addView(button("Sync now") { syncNow() })
        root.addView(button("Refresh local usage") { updatePreview() })
        status = TextView(this).apply { textSize=13f; setTextColor(0xFF207B55.toInt()); setPadding(0,14,0,8) }
        root.addView(status)
        preview = TextView(this).apply { textSize=14f; setTextColor(0xFF263B30.toInt()); setPadding(0,8,0,20) }
        root.addView(preview)
        root.addView(TextView(this).apply {
            text="Setup\n1. Run the Django backend on your laptop.\n2. Use the laptop's Wi-Fi IP address above, not 127.0.0.1.\n3. Log in on the web dashboard and copy the API token from Settings.\n4. Grant Usage Access, paste the token and tap Sync now.\n\nUse HTTPS for hosted deployments; HTTP is enabled for local development."
            textSize=13f; setTextColor(0xFF748078.toInt())
        })
        val scroll = ScrollView(this); scroll.addView(root); setContentView(scroll)
        updatePreview()
    }

    private fun button(label: String, action: () -> Unit) = Button(this).apply {
        text=label; isAllCaps=false; setOnClickListener { action() }
    }

    private fun hasAccess(): Boolean {
        val ops=getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        return ops.checkOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS, android.os.Process.myUid(), packageName)==AppOpsManager.MODE_ALLOWED
    }

    private fun collect(): JSONObject {
        val cal=Calendar.getInstance()
        cal.set(Calendar.HOUR_OF_DAY,0); cal.set(Calendar.MINUTE,0); cal.set(Calendar.SECOND,0); cal.set(Calendar.MILLISECOND,0)
        val manager=getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
        val stats=manager.queryUsageStats(UsageStatsManager.INTERVAL_DAILY,cal.timeInMillis,System.currentTimeMillis())
        val sums=stats.orEmpty().filter { it.totalTimeInForeground>0L && it.packageName!=packageName }
            .groupBy { it.packageName }.mapValues { (_,v)->v.sumOf { it.totalTimeInForeground } }.toList().sortedByDescending { it.second }
        val apps=JSONArray(); var total=0L
        for ((pkg,ms) in sums) {
            total+=ms
            val name=try { packageManager.getApplicationLabel(packageManager.getApplicationInfo(pkg,0)).toString() } catch (_:Exception) { pkg }
            apps.put(JSONObject().put("package_name",pkg).put("app_name",name).put("minutes",(ms/60000L).toInt()))
        }
        return JSONObject().put("date",SimpleDateFormat("yyyy-MM-dd",Locale.US).format(Date()))
            .put("total_minutes",(total/60000L).toInt()).put("apps",apps)
    }

    private fun updatePreview() {
        if (!hasAccess()) { preview.text="Usage Access is not enabled. Tap Grant Usage Access and enable Focus Reset."; status.text="Permission needed"; return }
        try { val r=collect(); preview.text="Today's reported foreground usage: ${r.optInt("total_minutes")} minutes\nApps detected: ${r.optJSONArray("apps")?.length() ?: 0}"; status.text="Usage Access granted" }
        catch(e:Exception) { status.text="Could not read usage: ${e.message}" }
    }

    private fun syncNow() {
        if (!hasAccess()) { Toast.makeText(this,"Grant Usage Access first.",Toast.LENGTH_LONG).show(); startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)); return }
        val base=api.text.toString().trim().trimEnd('/'); val key=token.text.toString().trim()
        if (base.isBlank() || key.isBlank()) { Toast.makeText(this,"Enter backend URL and token.",Toast.LENGTH_LONG).show(); return }
        getPreferences(MODE_PRIVATE).edit().putString("api",base).putString("token",key).apply()
        status.text="Collecting and syncing…"
        executor.execute {
            try {
                val record=collect()
                val conn=(URL("$base/api/usage/sync/").openConnection() as HttpURLConnection).apply {
                    requestMethod="POST"; connectTimeout=10000; readTimeout=15000; doOutput=true
                    setRequestProperty("Content-Type","application/json"); setRequestProperty("Authorization","Token $key")
                }
                conn.outputStream.use { it.write(record.toString().toByteArray(Charsets.UTF_8)) }
                val code=conn.responseCode
                val body=(if(code in 200..299) conn.inputStream else conn.errorStream)?.bufferedReader()?.use{it.readText()} ?: ""
                conn.disconnect()
                runOnUiThread {
                    if(code in 200..299) { status.text="Sync successful"; preview.text="Synced ${record.optInt("total_minutes")} minutes for ${record.optString("date")}."; Toast.makeText(this,"Screen time synced.",Toast.LENGTH_SHORT).show() }
                    else status.text="Sync failed (HTTP $code): ${body.take(160)}"
                }
            } catch(e:Exception) { runOnUiThread { status.text="Sync failed: ${e.message}" } }
        }
    }

    override fun onDestroy() { executor.shutdown(); super.onDestroy() }
}
