package com.lulu.pet

import android.Manifest
import android.annotation.SuppressLint
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.View
import android.webkit.CookieManager
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.lulu.pet.settings.SettingsActivity

/**
 * 主界面就是网页版那一份：上面是噜噜，下面是聊天框。
 *
 * 走网页而不是原生重写，是因为云端登录与模型调用只有官方 Web SDK 这一条路 ——
 * 原生自己拼 REST 属于未公开用法，接口一变就崩。桌面悬浮窗仍然保持原生（网页做不到）。
 */
class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView
    private lateinit var offline: View

    private val overlayPermissionLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {
            if (Settings.canDrawOverlays(this)) startPet() else Toast.makeText(
                this, R.string.overlay_permission_hint, Toast.LENGTH_SHORT
            ).show()
        }

    private val notificationPermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) {
            startPet()
        }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        web = findViewById(R.id.web)
        offline = findViewById(R.id.offline)

        web.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            cacheMode = WebSettings.LOAD_DEFAULT
            mediaPlaybackRequiresUserGesture = false
            // 加上标记，网页据此隐藏在 WebView 里走不通的微信扫码登录
            userAgentString = userAgentString + " LuluPetAndroid"
        }

        CookieManager.getInstance().setAcceptCookie(true)
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, true)

        web.webViewClient = object : WebViewClient() {
            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                offline.visibility = View.GONE
            }

            override fun onReceivedError(
                view: WebView?,
                request: WebResourceRequest?,
                error: WebResourceError?,
            ) {
                if (request?.isForMainFrame == true) offline.visibility = View.VISIBLE
            }
        }
        web.webChromeClient = WebChromeClient()

        web.loadUrl(APP_URL)

        findViewById<Button>(R.id.btn_retry).setOnClickListener {
            offline.visibility = View.GONE
            web.loadUrl(APP_URL)
        }
        findViewById<Button>(R.id.btn_more).setOnClickListener { showMenu() }
    }

    override fun onResume() {
        super.onResume()
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (web.canGoBack()) web.goBack() else super.onBackPressed()
    }

    private fun showMenu() {
        val running = PetService.isRunning()
        val items = arrayOf(
            if (running) "停止桌面悬浮" else "在桌面显示噜噜",
            "设置",
            "重新加载页面"
        )
        AlertDialog.Builder(this)
            .setItems(items) { _, which ->
                when (which) {
                    0 -> if (running) stopPet() else startPet()
                    1 -> startActivity(Intent(this, SettingsActivity::class.java))
                    2 -> web.reload()
                }
            }
            .show()
    }

    private fun startPet() {
        if (!Settings.canDrawOverlays(this)) {
            Toast.makeText(this, R.string.overlay_permission_hint, Toast.LENGTH_SHORT).show()
            requestOverlayPermission()
            return
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
            != PackageManager.PERMISSION_GRANTED
        ) {
            notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            return
        }
        val intent = Intent(this, PetService::class.java).setAction(PetService.ACTION_START)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
        Toast.makeText(this, "噜噜已经跑到桌面上了", Toast.LENGTH_SHORT).show()
    }

    private fun stopPet() {
        stopService(Intent(this, PetService::class.java).setAction(PetService.ACTION_STOP))
        Toast.makeText(this, "桌面上的噜噜收回来了", Toast.LENGTH_SHORT).show()
    }

    private fun requestOverlayPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val intent = Intent(
                Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:$packageName")
            )
            overlayPermissionLauncher.launch(intent)
        } else {
            startPet()
        }
    }

    companion object {
        /** 线上网页版地址；带 sharecode 才能在发布域名下正常访问。 */
        const val APP_URL =
            "https://wbapp-gbyys9j25fx0srxlke1txs.app.workbuddy.host/?sharecode=GGII4BMCNO"
    }
}
