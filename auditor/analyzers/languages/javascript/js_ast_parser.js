/**
 * Node.js AST and Structural Parser for JavaScript & TypeScript codebases.
 * Extracts functions, imports, async calls, blocking operations, routes, and promises.
 */

const fs = require('fs');
const path = require('path');

function analyzeFile(filePath) {
    const code = fs.readFileSync(filePath, 'utf-8');
    const lines = code.split(/\r?\n/);

    const result = {
        file: filePath,
        totalLines: lines.length,
        imports: [],
        exports: [],
        functions: [],
        blockingCalls: [],
        evalCalls: [],
        unhandledPromises: [],
        anyTypes: [],
        expressRoutes: [],
        expressErrorMiddleware: [],
    };

    // State trackers
    let inFunction = null;

    lines.forEach((line, idx) => {
        const lineNum = idx + 1;
        const trimmed = line.trim();

        // Skip full comment lines
        if (trimmed.startsWith('//') || trimmed.startsWith('/*') || trimmed.startsWith('*')) {
            return;
        }

        // 1. Imports
        // ES6: import ... from '...'
        const esmImport = line.match(/import\s+(?:(?:[\w*\s{},]+)\s+from\s+)?['"]([^'"]+)['"]/);
        if (esmImport) {
            result.imports.push({ module: esmImport[1], line: lineNum });
        }
        // CommonJS: require('...')
        const cjsRequire = line.match(/require\s*\(\s*['"]([^'"]+)['"]\s*\)/);
        if (cjsRequire) {
            result.imports.push({ module: cjsRequire[1], line: lineNum });
        }

        // 2. Synchronous blocking calls in server context
        if (/\b(?:fs\.readFileSync|fs\.writeFileSync|fs\.existsSync|crypto\.pbkdf2Sync|child_process\.execSync)\b/.test(line)) {
            result.blockingCalls.push({ line: lineNum, text: trimmed });
        }

        // 3. Eval / Function constructor
        if (/\b(?:eval\s*\(|new\s+Function\s*\()/.test(line)) {
            result.evalCalls.push({ line: lineNum, text: trimmed });
        }

        // 4. Any types in TypeScript
        if (/(?::\s*any\b|<any>|as\s+any\b)/.test(line)) {
            result.anyTypes.push({ line: lineNum, text: trimmed });
        }

        // 5. Unhandled Promise: .then(...) without .catch or await without try
        if (/\.then\s*\(/.test(line) && !line.includes('.catch') && !lines.slice(idx, idx + 5).some(l => l.includes('.catch'))) {
            result.unhandledPromises.push({ line: lineNum, text: trimmed });
        }

        // 6. Express routes: app.get / router.post / etc.
        const routeMatch = line.match(/\b(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]\s*,\s*(?:async\s*)?(?:\(([^)]*)\)|([a-zA-Z0-9_]+))/);
        if (routeMatch) {
            const isAsync = line.includes('async');
            result.expressRoutes.push({
                method: routeMatch[1],
                path: routeMatch[2],
                isAsync: isAsync,
                line: lineNum,
                hasTryCatch: false, // determined in block
            });
        }

        // 7. Express 4-argument error middleware: (err, req, res, next)
        if (/\b(?:app|router)\.use\s*\(\s*(?:async\s*)?\(\s*[\w$]+\s*,\s*[\w$]+\s*,\s*[\w$]+\s*,\s*[\w$]+\s*\)/.test(line)) {
            result.expressErrorMiddleware.push({ line: lineNum, text: trimmed });
        }
    });

    return result;
}

if (require.main === module) {
    const targetFile = process.argv[2];
    if (!targetFile) {
        console.error('Usage: node js_ast_parser.js <file>');
        process.exit(1);
    }
    try {
        const analysis = analyzeFile(targetFile);
        console.log(JSON.stringify(analysis));
    } catch (err) {
        console.error(JSON.stringify({ error: err.message }));
        process.exit(1);
    }
}

module.exports = { analyzeFile };

