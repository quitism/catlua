const vscode = require('vscode');
const { spawn } = require('child_process');

function activate(context) {
    const diagnosticCollection = vscode.languages.createDiagnosticCollection('catlua');
    context.subscriptions.push(diagnosticCollection);

    let lintTimeout;

    vscode.workspace.onDidChangeTextDocument((event) => {
        const document = event.document;
        if (document.languageId !== 'catlua') return;

        clearTimeout(lintTimeout);
        
        lintTimeout = setTimeout(() => {
            const config = vscode.workspace.getConfiguration('catlua');
            const compilerPath = config.get('compilerPath'); 

            if (!compilerPath) return;

            const pyProcess = spawn('python', [compilerPath, document.uri.fsPath, '--lint', '--stdin']);
            
            let stdout = "";
            pyProcess.stdout.on('data', (data) => { stdout += data.toString(); });
            
            pyProcess.on('close', (code) => {
                diagnosticCollection.clear();
                try {
                    const diagnostics = JSON.parse(stdout);
                    const vsDiagnostics = diagnostics.map(diag => {
                        const lineStr = Math.max(0, diag.line - 1); 
                        const lineObj = document.lineAt(lineStr);
                        const range = new vscode.Range(
                            lineStr, 
                            lineObj.firstNonWhitespaceCharacterIndex, 
                            lineStr, 
                            lineObj.text.length
                        );
                        const severity = diag.severity === "warning" 
                            ? vscode.DiagnosticSeverity.Warning 
                            : vscode.DiagnosticSeverity.Error;
                        return new vscode.Diagnostic(range, diag.msg, severity);
                    });
                    diagnosticCollection.set(document.uri, vsDiagnostics);
                } catch (e) {

                }
            });

            pyProcess.stdin.write(document.getText());
            pyProcess.stdin.end();

        }, 500);
    });

    const provider = vscode.languages.registerCompletionItemProvider('catlua', {
        provideCompletionItems(document, position, token, context) {
            const items = [];

            const makeItem = (name, kind, detail, doc) => {
                const item = new vscode.CompletionItem(name, kind);
                item.detail = detail;
                item.documentation = new vscode.MarkdownString(doc);
                items.push(item);
            };

            makeItem('LocalPlayer', vscode.CompletionItemKind.Class, 'Service', 'Access local visitor info (Name, UserId, DisplayName)');
            makeItem('UserInputService', vscode.CompletionItemKind.Class, 'Service', 'Check inputs and get mouse location');
            makeItem('Camera', vscode.CompletionItemKind.Class, 'Service', 'Access viewport size');

            makeItem('print', vscode.CompletionItemKind.Function, 'print(any)', 'Logs to the console');
            makeItem('warn', vscode.CompletionItemKind.Function, 'warn(any)', 'Warns to the console');
            makeItem('error', vscode.CompletionItemKind.Function, 'error(any)', 'Errors to the console and halts execution');
            makeItem('wait', vscode.CompletionItemKind.Function, 'wait(seconds)', 'Pauses execution for a given amount of seconds');
            makeItem('playAudio', vscode.CompletionItemKind.Function, 'playAudio(id) -> audioVar', 'Plays a sound with the given asset ID and optionally returns a variable to control it');
            makeItem('tween', vscode.CompletionItemKind.Function, 'tween(obj, prop, val, time, style, dir)', 'Tweens a property of an object');
            
            makeItem('local', vscode.CompletionItemKind.Keyword, 'Keyword', 'Declares a variable accessible only to the current event');
            makeItem('global', vscode.CompletionItemKind.Keyword, 'Keyword', 'Declares a variable accessible by all scripts');
            makeItem('object', vscode.CompletionItemKind.Keyword, 'Keyword', 'Declares a variable accessible only to the current script element');

            return items;
        }
    });

    context.subscriptions.push(provider);
}

function deactivate() {}

module.exports = { activate, deactivate };