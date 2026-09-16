using System.Text;
using UnityEngine;

/// <summary>
/// Animator ウィンドウを使わずに MorseChar を動かすテスト用コンポーネント。
///
/// 使い方:
///   1. crt_tv（Animator を持つオブジェクト）に Add Component で付ける
///   2. Play する
///   3. Inspector の Index スライダーを動かす
///
/// Game ビューの左上に「送っている値」と「実際にマテリアルへ届いた値」を並べて出す。
/// 届いていなければ Animator 側、届いているのに文字が出なければマテリアル側の問題。
/// 確認が済んだら外してよい。VRChat には持っていかない。
/// </summary>
public class MorseCharTester : MonoBehaviour
{
    // vrc_morse_osc.py の CHARSET と一致させること。
    const string CHARSET = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,?'!/()&:;=+-_\"$@";
    const string PARAM = "MorseChar";

    [Tooltip("0 = 空白, 1 = A ... 54 = @")]
    [Range(0, 54)] public int index = 1;

    Animator animator;
    Renderer screen;
    string setupError = "";

    void Start()
    {
        animator = GetComponent<Animator>();
        if (animator == null)
        {
            setupError = "このオブジェクトに Animator がない。crt_tv に付けること";
        }
        else if (animator.runtimeAnimatorController == null)
        {
            setupError = "Animator の Controller が空。MorseFX を入れること";
        }
        else
        {
            bool found = false;
            StringBuilder names = new StringBuilder();
            foreach (AnimatorControllerParameter p in animator.parameters)
            {
                names.Append(p.name).Append("(").Append(p.type).Append(") ");
                if (p.name == PARAM && p.type == AnimatorControllerParameterType.Float) found = true;
            }
            if (!found)
            {
                setupError = "Controller に Float の " + PARAM + " がない。今あるのは: " + names;
            }
        }

        foreach (Renderer r in GetComponentsInChildren<Renderer>())
        {
            if (r.gameObject.name == "TV_Screen") screen = r;
        }
        if (screen == null && setupError.Length == 0)
        {
            setupError = "子に TV_Screen という名前の Renderer がない";
        }

        if (setupError.Length > 0) Debug.LogError("[MorseCharTester] " + setupError, this);
    }

    void Update()
    {
        if (animator != null && setupError.Length == 0)
        {
            animator.SetFloat(PARAM, index / (float)(CHARSET.Length - 1));
        }
    }

    void OnGUI()
    {
        GUIStyle style = new GUIStyle(GUI.skin.label);
        style.fontSize = 18;
        style.normal.textColor = Color.white;

        string line1, line2, line3;
        if (setupError.Length > 0)
        {
            line1 = "設定エラー: " + setupError;
            line2 = line3 = "";
        }
        else
        {
            float v = index / (float)(CHARSET.Length - 1);
            int col = index % 8, row = index / 8;
            line1 = "送信: MorseChar = " + v.ToString("F4") + "  -> index " + index +
                    " '" + CHARSET[index] + "'  期待 offset (" +
                    (col / 8f).ToString("F3") + ", " + (1f - (row + 1) / 8f).ToString("F3") + ")";

            Vector4 st = screen.material.GetVector("_MainTex_ST");
            line2 = "実際: TV_Screen の _MainTex_ST  tiling (" + st.x.ToString("F3") + ", " +
                    st.y.ToString("F3") + ")  offset (" + st.z.ToString("F3") + ", " + st.w.ToString("F3") + ")";

            AnimatorStateInfo info = animator.GetCurrentAnimatorStateInfo(0);
            line3 = "Animator: normalizedTime " + info.normalizedTime.ToString("F4") +
                    "  (MorseChar と同じ値になっていれば Motion Time は効いている)";
        }

        GUI.Label(new Rect(10, 10, 1200, 30), line1, style);
        GUI.Label(new Rect(10, 40, 1200, 30), line2, style);
        GUI.Label(new Rect(10, 70, 1200, 30), line3, style);
    }
}
