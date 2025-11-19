package com.example.miceverywhere

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.ImageFormat
import android.graphics.Rect
import android.graphics.YuvImage
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.EditText
import android.widget.ImageButton
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.net.Socket
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {

    // Elementos da Tela
    private lateinit var viewFinder: PreviewView
    private lateinit var etIp: EditText
    private lateinit var btnConnect: Button
    private lateinit var btnSwitch: ImageButton

    // Executor da Câmera
    private val cameraExecutor = Executors.newSingleThreadExecutor()

    // Estado da Câmera (Começa com a traseira)
    private var currentCameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

    // Rede - Vídeo
    private var socketVideo: Socket? = null
    private var outVideo: DataOutputStream? = null

    // Rede - Áudio
    private var socketAudio: Socket? = null

    // Controle de Estado
    private var isStreaming = false
    private var streamJob: Job? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // 1. Vincular componentes
        viewFinder = findViewById(R.id.viewFinder)
        etIp = findViewById(R.id.etIpAddress)
        btnConnect = findViewById(R.id.btnConnect)
        btnSwitch = findViewById(R.id.btnSwitchCamera)

        // 2. Pedir permissões (Agora inclui Áudio)
        if (allPermissionsGranted()) {
            startCamera()
        } else {
            ActivityCompat.requestPermissions(this, REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS)
        }

        // 3. Botão Conectar
        btnConnect.setOnClickListener {
            if (isStreaming) {
                disconnect()
            } else {
                val ip = etIp.text.toString()
                if (ip.length < 7) Toast.makeText(this, "IP Inválido", Toast.LENGTH_SHORT).show()
                else connectAndStream(ip)
            }
        }

        // 4. Botão Trocar Câmera
        btnSwitch.setOnClickListener {
            // Inverte a seleção
            currentCameraSelector = if (currentCameraSelector == CameraSelector.DEFAULT_BACK_CAMERA) {
                CameraSelector.DEFAULT_FRONT_CAMERA
            } else {
                CameraSelector.DEFAULT_BACK_CAMERA
            }
            // Reinicia a câmera com a nova escolha
            startCamera()
        }
    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)

        cameraProviderFuture.addListener({
            val cameraProvider: ProcessCameraProvider = cameraProviderFuture.get()

            val preview = Preview.Builder()
                .build()
                .also { it.setSurfaceProvider(viewFinder.surfaceProvider) }

            val imageAnalyzer = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
                .also {
                    it.setAnalyzer(cameraExecutor) { image ->
                        processImage(image)
                    }
                }

            try {
                cameraProvider.unbindAll() // Remove a câmera anterior
                // Vincula a nova (Frontal ou Traseira)
                cameraProvider.bindToLifecycle(this, currentCameraSelector, preview, imageAnalyzer)
            } catch (exc: Exception) {
                Log.e("Webdroid", "Erro ao abrir câmera", exc)
            }

        }, ContextCompat.getMainExecutor(this))
    }

    // --- Processamento de Vídeo ---
    private fun processImage(image: ImageProxy) {
        if (!isStreaming || outVideo == null) {
            image.close()
            return
        }
        try {
            val jpegBytes = yuvToJpeg(image)
            synchronized(this) {
                outVideo?.let { out ->
                    out.writeInt(jpegBytes.size)
                    out.write(jpegBytes)
                    out.flush()
                }
            }
        } catch (e: Exception) {
            Log.e("Webdroid", "Erro envio vídeo", e)
            viewFinder.post { disconnect() }
        } finally {
            image.close()
        }
    }

    // --- Processamento de Áudio (Thread Separada) ---
    private fun startAudioStream(ip: String) {
        Thread {
            try {
                // Configuração padrão de microfone (Mono, 16bit, 44100Hz)
                val sampleRate = 44100
                val channelConfig = AudioFormat.CHANNEL_IN_MONO
                val audioFormat = AudioFormat.ENCODING_PCM_16BIT
                val minBufSize = AudioRecord.getMinBufferSize(sampleRate, channelConfig, audioFormat)

                if (ActivityCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                    return@Thread
                }

                val recorder = AudioRecord(MediaRecorder.AudioSource.MIC, sampleRate, channelConfig, audioFormat, minBufSize)
                val buffer = ByteArray(minBufSize)

                Log.d("Webdroid", "Conectando Áudio em $ip:5001")
                socketAudio = Socket(ip, 5001) // Porta 5001
                val outAudio = socketAudio!!.getOutputStream()

                recorder.startRecording()

                while (isStreaming) {
                    val read = recorder.read(buffer, 0, buffer.size)
                    if (read > 0) {
                        outAudio.write(buffer, 0, read)
                    }
                }

                recorder.stop()
                recorder.release()
                outAudio.close()

            } catch (e: Exception) {
                Log.e("Webdroid", "Erro Áudio: ${e.message}")
            }
        }.start()
    }

    // --- Conexão Geral ---
    private fun connectAndStream(ip: String) {
        streamJob = CoroutineScope(Dispatchers.IO).launch {
            try {
                withContext(Dispatchers.Main) {
                    btnConnect.text = "CONECTANDO..."
                    btnConnect.isEnabled = false
                }

                // 1. Conecta Vídeo (Porta 5000)
                socketVideo = Socket(ip, 5000)
                outVideo = DataOutputStream(socketVideo!!.getOutputStream())

                isStreaming = true

                // 2. Inicia Áudio em paralelo (Porta 5001)
                startAudioStream(ip)

                withContext(Dispatchers.Main) {
                    btnConnect.text = "DESCONECTAR"
                    btnConnect.isEnabled = true
                    btnConnect.setBackgroundColor(0xFFB00020.toInt()) // Vermelho
                    etIp.isEnabled = false
                    Toast.makeText(applicationContext, "Ao Vivo (Vídeo + Áudio)!", Toast.LENGTH_SHORT).show()
                }

            } catch (e: Exception) {
                Log.e("Webdroid", "Erro Conexão", e)
                withContext(Dispatchers.Main) {
                    disconnectUI()
                    Toast.makeText(applicationContext, "Erro: ${e.message}", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    private fun disconnect() {
        isStreaming = false
        try {
            outVideo?.close()
            socketVideo?.close()
            socketAudio?.close()
        } catch (e: Exception) {
            e.printStackTrace()
        }
        socketVideo = null
        outVideo = null
        socketAudio = null

        if (Thread.currentThread() == android.os.Looper.getMainLooper().thread) {
            disconnectUI()
        } else {
            viewFinder.post { disconnectUI() }
        }
    }

    private fun disconnectUI() {
        btnConnect.text = "CONECTAR TUDO"
        btnConnect.isEnabled = true
        btnConnect.setBackgroundColor(0xFF6200EE.toInt())
        etIp.isEnabled = true
    }

    private fun yuvToJpeg(image: ImageProxy): ByteArray {
        val yBuffer = image.planes[0].buffer
        val uBuffer = image.planes[1].buffer
        val vBuffer = image.planes[2].buffer
        val ySize = yBuffer.remaining()
        val uSize = uBuffer.remaining()
        val vSize = vBuffer.remaining()
        val nv21 = ByteArray(ySize + uSize + vSize)
        yBuffer.get(nv21, 0, ySize)
        vBuffer.get(nv21, ySize, vSize)
        uBuffer.get(nv21, ySize + vSize, uSize)
        val yuvImage = YuvImage(nv21, ImageFormat.NV21, image.width, image.height, null)
        val out = ByteArrayOutputStream()
        yuvImage.compressToJpeg(Rect(0, 0, yuvImage.width, yuvImage.height), 50, out)
        return out.toByteArray()
    }

    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(baseContext, it) == PackageManager.PERMISSION_GRANTED
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_CODE_PERMISSIONS) {
            if (allPermissionsGranted()) {
                startCamera()
            } else {
                Toast.makeText(this, "Permissões negadas.", Toast.LENGTH_SHORT).show()
                finish()
            }
        }
    }

    companion object {
        private const val REQUEST_CODE_PERMISSIONS = 10
        private val REQUIRED_PERMISSIONS = arrayOf(Manifest.permission.CAMERA, Manifest.permission.RECORD_AUDIO)
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
        disconnect()
    }
}