using System;
using System.Text;
using UnityEditor;
using UnityEngine;

/// <summary>
/// モールス表示用のアニメーションクリップを 1 本生成する。
///
/// 使い方:
///   1. TV をアバターの子に置く（Animator を持つ階層の下に入れる）
///   2. アトラスを貼った TV_Screen を選択する
///   3. Tools → Morse → MorseChar クリップを生成
///
/// キーの時刻を半フレームずらしてあるのが肝。素直にキー i をフレーム i へ置くと、
/// リモートの 8bit 量子化が下振れしたときキー境界を割って 1 つ前の文字が出る。
/// しかもローカルでは量子化されないので自分では気づけない。詳細は CLAUDE.md 4-2。
/// </summary>
public static class MorseCharClipGenerator
{
    // vrc_morse_osc.py の CHARSET と完全に一致させること。ずれると全文字が狂う。
    const string CHARSET = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,?'!/()&:;=+-_\"$@";

    const int COLS = 8;
    const int ROWS = 8;

    // 半フレームずらしを整数フレームで表すために 120fps にする。60fps 換算の半分。
    const float FPS = 120f;

    // Standard シェーダーは Emission Map も _MainTex_ST の UV で引く。
    // Poiyomi などに差し替えたら "material._EmissionMap_ST" などに変える。
    const string PROP = "material._MainTex_ST";

    [MenuItem("Tools/Morse/MorseChar クリップを生成")]
    static void Generate()
    {
        GameObject go = Selection.activeGameObject;
        if (go == null)
        {
            Fail("アトラスを貼った TV_Screen を選んでから実行してください。");
            return;
        }

        Renderer renderer = go.GetComponent<Renderer>();
        if (renderer == null)
        {
            Fail("\"" + go.name + "\" に Renderer がありません。TV_Screen を選んでください。");
            return;
        }

        Transform root = FindAnimatorRoot(go.transform);
        if (root == null)
        {
            Fail("Animator を持つ親が見つかりません。\n\n" +
                 "TV をアバターの子に置いてから実行してください。\n" +
                 "ここで決まるパスがずれると、クリップは何も動かしません。");
            return;
        }

        string path = AnimationUtility.CalculateTransformPath(go.transform, root);

        int n = CHARSET.Length;
        int span = n - 1;

        // グリフ 55 個 + 末尾のダミー 1 個。
        Keyframe[] keysZ = new Keyframe[n + 1];
        Keyframe[] keysW = new Keyframe[n + 1];

        for (int i = 0; i < n; i++)
        {
            // 配置B: キー i はフレーム 2i-1（i=0 だけフレーム 0）。
            // Motion Time の着地点フレーム 2i が、キー区間のちょうど中央になる。
            float frame = (i == 0) ? 0f : (2 * i - 1);
            float time = frame / FPS;
            keysZ[i] = Step(time, (i % COLS) / (float)COLS);
            keysW[i] = Step(time, 1f - ((i / COLS) + 1) / (float)ROWS);
        }

        // 末尾のダミー。クリップ長を 108 フレームに固定して、MorseChar = 1.0 が
        // 下振れしても最後のグリフに留まるようにする。値は最後のグリフと同じ。
        float endTime = (2 * span) / FPS;
        keysZ[n] = Step(endTime, keysZ[n - 1].value);
        keysW[n] = Step(endTime, keysW[n - 1].value);

        AnimationCurve curveZ = MakeSteppedCurve(keysZ);
        AnimationCurve curveW = MakeSteppedCurve(keysW);

        AnimationClip clip = new AnimationClip();
        clip.frameRate = FPS;

        Type rendererType = renderer.GetType();
        AnimationUtility.SetEditorCurve(
            clip, EditorCurveBinding.FloatCurve(path, rendererType, PROP + ".z"), curveZ);
        AnimationUtility.SetEditorCurve(
            clip, EditorCurveBinding.FloatCurve(path, rendererType, PROP + ".w"), curveW);

        // Unity は Vector 型プロパティの一部成分だけをアニメーションすると、残りの成分を
        // 0 で書き込む。z/w だけ動かすと Play した瞬間に Tiling (x/y) が 0 に潰れて
        // 画面が真っ暗になる。実際に起きた。だから x/y も定数キーで持たせる。
        AnimationCurve tileX = AnimationCurve.Constant(0f, endTime, 1f / COLS);
        AnimationCurve tileY = AnimationCurve.Constant(0f, endTime, 1f / ROWS);
        AnimationUtility.SetEditorCurve(
            clip, EditorCurveBinding.FloatCurve(path, rendererType, PROP + ".x"), tileX);
        AnimationUtility.SetEditorCurve(
            clip, EditorCurveBinding.FloatCurve(path, rendererType, PROP + ".y"), tileY);

        AnimationClipSettings settings = AnimationUtility.GetAnimationClipSettings(clip);
        settings.loopTime = false;
        AnimationUtility.SetAnimationClipSettings(clip, settings);

        string savePath = EditorUtility.SaveFilePanelInProject(
            "MorseChar クリップの保存先", "MorseChar", "anim", "");
        if (string.IsNullOrEmpty(savePath)) return;

        AssetDatabase.CreateAsset(clip, savePath);
        AssetDatabase.SaveAssets();

        Verify(clip, curveZ, curveW, path, savePath, renderer);
    }

    /// <summary>
    /// 前提を満たしていないときに止める。Console を見ていなくても気づけるよう
    /// ダイアログも出す。
    /// </summary>
    static void Fail(string message)
    {
        EditorUtility.DisplayDialog("MorseChar クリップ生成", message, "OK");
        Debug.LogError("[MorseChar] " + message);
    }

    /// <summary>一番上の Animator を持つ階層を返す。アバタールートのつもり。</summary>
    static Transform FindAnimatorRoot(Transform t)
    {
        Transform found = null;
        for (Transform c = t; c != null; c = c.parent)
        {
            if (c.GetComponent<Animator>() != null) found = c;
        }
        return found;
    }

    static Keyframe Step(float time, float value)
    {
        return new Keyframe(time, value, float.PositiveInfinity, float.PositiveInfinity);
    }

    static AnimationCurve MakeSteppedCurve(Keyframe[] keys)
    {
        AnimationCurve curve = new AnimationCurve(keys);
        for (int i = 0; i < curve.length; i++)
        {
            AnimationUtility.SetKeyLeftTangentMode(curve, i, AnimationUtility.TangentMode.Constant);
            AnimationUtility.SetKeyRightTangentMode(curve, i, AnimationUtility.TangentMode.Constant);
        }
        return curve;
    }

    /// <summary>
    /// リモートに届く 8bit 量子化値を実際に流し込んで、全グリフが正しく出るか確かめる。
    /// ローカルでは量子化されないので、この検算をしないとズレに気づけない。
    /// </summary>
    static void Verify(AnimationClip clip, AnimationCurve curveZ, AnimationCurve curveW,
                       string path, string savePath, Renderer renderer)
    {
        int n = CHARSET.Length;
        int span = n - 1;
        StringBuilder bad = new StringBuilder();
        int badCount = 0;

        for (int i = 0; i < n; i++)
        {
            // VRChat がリモート向けに float を 8bit へ落とす。
            float p = Mathf.Round(i / (float)span * 255f) / 255f;
            float time = p * clip.length;
            int col = Mathf.RoundToInt(curveZ.Evaluate(time) * COLS);
            int row = ROWS - 1 - Mathf.RoundToInt(curveW.Evaluate(time) * ROWS);
            int got = row * COLS + col;
            if (got != i)
            {
                badCount++;
                string shown = (got >= 0 && got < n) ? "'" + CHARSET[got] + "'" : "範囲外";
                bad.AppendLine("  index " + i + " '" + CHARSET[i] + "' のはずが " + shown + " になる");
            }
        }

        string head =
            "MorseChar クリップを生成しました\n" +
            "  保存先: " + savePath + "\n" +
            "  パス: \"" + path + "\"  (" + renderer.GetType().Name + ")\n" +
            "  グリフ " + n + " 個 + 末尾ダミー 1 = キー " + (n + 1) + " 個 x 2 プロパティ (offset)\n" +
            "  Tiling (x/y) は定数 " + (1f / COLS).ToString("F3") + " で同梱\n" +
            "  クリップ長: " + clip.length.ToString("F4") + " 秒 (" +
            (clip.length * FPS).ToString("F0") + " フレーム @ " + FPS + "fps)\n";

        if (badCount == 0)
        {
            Debug.Log(head + "  8bit 量子化の検算: 全 " + n + " グリフ OK", clip);
        }
        else
        {
            Debug.LogError(head + "  8bit 量子化の検算: " + badCount + " 文字がずれる\n" + bad, clip);
        }
    }
}
