// Parse syntax without evaluating repository code or running package scripts.
const fs = require('node:fs');
const path = require('node:path');
const { root, paths } = JSON.parse(fs.readFileSync(0, 'utf8'));
const allowed = new Set(paths);
const result = {};
const ts = require('typescript');
for (const relative of paths) {
  const filename = path.join(root, relative);
  const source = ts.createSourceFile(filename, fs.readFileSync(filename, 'utf8'), ts.ScriptTarget.Latest, true);
  const record = { symbols: [], imports: [], routes: [], diagnostics: [] };
  const counts = new Map();
  const line = n => source.getLineAndCharacterOfPosition(n.getStart(source)).line + 1;
  function symbol(n, name, type = 'source') {
    const count = counts.get(name) || 0;
    counts.set(name, count + 1);
    record.symbols.push({ symbol: name + (count ? `:${count}` : ''), type, line: line(n), end_line: source.getLineAndCharacterOfPosition(n.end).line + 1 });
  }
  function importModule(n, module) {
    const resolved = ts.resolveModuleName(module, filename, { moduleResolution: ts.ModuleResolutionKind.Bundler, allowJs: true, jsx: ts.JsxEmit.Preserve }, ts.sys).resolvedModule;
    const local = resolved && path.relative(root, resolved.resolvedFileName).split(path.sep).join('/');
    record.imports.push({ module, local: module.startsWith('.'), resolved: allowed.has(local) ? local : null, line: line(n) });
  }
  function visit(n, prefix = '') {
    if ((ts.isImportDeclaration(n) || ts.isExportDeclaration(n)) && n.moduleSpecifier && ts.isStringLiteral(n.moduleSpecifier)) importModule(n, n.moduleSpecifier.text);
    if (ts.isFunctionDeclaration(n) || ts.isClassDeclaration(n) || ts.isMethodDeclaration(n) || ts.isInterfaceDeclaration(n) || ts.isTypeAliasDeclaration(n)) {
      if (n.name) {
        const name = prefix + n.name.getText(source);
        symbol(n, name, /^[A-Z]/.test(name) && /\.[jt]sx$/.test(relative) ? 'ui' : 'source');
        ts.forEachChild(n, child => visit(child, name + '.'));
        return;
      }
    }
    if (ts.isVariableDeclaration(n) && (n.initializer && (ts.isArrowFunction(n.initializer) || ts.isFunctionExpression(n.initializer)))) symbol(n, prefix + n.name.getText(source), /^[A-Z]/.test(n.name.getText(source)) && /\.[jt]sx$/.test(relative) ? 'ui' : 'source');
    if (ts.isCallExpression(n)) {
      const callee = n.expression.getText(source);
      const arg = n.arguments[0];
      if (n.expression.kind === ts.SyntaxKind.ImportKeyword || callee === 'require') {
        if (arg && ts.isStringLiteral(arg)) importModule(n, arg.text);
        else record.diagnostics.push({ kind: 'dynamic-import', line: line(n), message: 'Nonliteral module loading is unresolved.' });
      }
      if (/^(test|it)(\.(only|skip))?$/.test(callee) && arg && ts.isStringLiteral(arg)) symbol(n, prefix + arg.text, 'test');
      if (ts.isPropertyAccessExpression(n.expression) && /^(get|post|put|patch|delete|route|all)$/.test(n.expression.name.text)) {
        if (arg && ts.isStringLiteral(arg) && arg.text.startsWith('/')) record.routes.push({ method: n.expression.name.text.toUpperCase(), route: arg.text, line: line(n) });
        else if (arg && (callee.startsWith('app.') || callee.startsWith('router.'))) record.diagnostics.push({ kind: 'dynamic-route', line: line(n), message: 'Nonliteral route requires source review.' });
      }
    }
    ts.forEachChild(n, child => visit(child, prefix));
  }
  visit(source);
  for (const diagnostic of source.parseDiagnostics) record.diagnostics.push({ kind: 'parse-error', line: source.getLineAndCharacterOfPosition(diagnostic.start || 0).line + 1, message: ts.flattenDiagnosticMessageText(diagnostic.messageText, ' ') });
  result[relative] = record;
}
process.stdout.write(JSON.stringify(result));
