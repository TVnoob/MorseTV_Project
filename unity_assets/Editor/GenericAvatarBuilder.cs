using UnityEditor;
using UnityEngine;

/// <summary>
/// 人型でないアバター用に Generic Avatar アセットを作り、Animator に割り当てる。
///
/// なぜ要るか: Animator の Avatar 欄が None だと、VRChat は AV3（Playable Layers と
/// Expression Parameters）を初期化せず、素の Animator だけを動かす。ループ再生は動くのに
/// Expression Parameters が OSC に出てこない、という症状になる。OBJ 由来のモデルは
/// Rig を Generic にしても Avatar アセットが生成されないことがあるので、ここで作る。
///
/// 使い方: アバターのルート（Animator が付いているオブジェクト）を選んで
///   Tools → Morse → Generic Avatar を作って Animator に割り当て
/// </summary>
public static class GenericAvatarBuilder
{
    [MenuItem("Tools/Morse/Generic Avatar を作って Animator に割り当て")]
    static void Build()
    {
        GameObject go = Selection.activeGameObject;
        if (go == null)
        {
            Fail("アバターのルート（Animator が付いているオブジェクト）を選んでください。");
            return;
        }
        Animator animator = go.GetComponent<Animator>();
        if (animator == null)
        {
            Fail("\"" + go.name + "\" に Animator がありません。");
            return;
        }

        Avatar avatar = AvatarBuilder.BuildGenericAvatar(go, "");
        if (avatar == null || !avatar.isValid)
        {
            Fail("Generic Avatar を作れませんでした。");
            return;
        }
        avatar.name = go.name + "Avatar";

        string path = AssetDatabase.GenerateUniqueAssetPath("Assets/" + avatar.name + ".asset");
        AssetDatabase.CreateAsset(avatar, path);
        AssetDatabase.SaveAssets();

        Undo.RecordObject(animator, "Assign Generic Avatar");
        animator.avatar = avatar;
        EditorUtility.SetDirty(animator);
        PrefabUtility.RecordPrefabInstancePropertyModifications(animator);

        Debug.Log("Generic Avatar を作成して割り当てました: " + path +
                  "  (isValid=" + avatar.isValid + ", isHuman=" + avatar.isHuman + ")", avatar);
        EditorUtility.DisplayDialog("Generic Avatar",
            "作成: " + path + "\n\nAnimator の Avatar 欄に入れました。\n" +
            "このあと Ctrl+S でシーンを保存し、Build & Publish をやり直してください。", "OK");
    }

    static void Fail(string message)
    {
        EditorUtility.DisplayDialog("Generic Avatar", message, "OK");
        Debug.LogError("[GenericAvatarBuilder] " + message);
    }
}
