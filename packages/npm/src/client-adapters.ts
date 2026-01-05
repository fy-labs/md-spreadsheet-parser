
export function clientSideToModels(headers: string[] | undefined | null, rows: any[][], schemaCls: any): any[] | null {
    // Client-Side Schema Support
    if (typeof schemaCls === 'object' && schemaCls !== null) {
        if (!headers) throw new Error('Table must have headers for client-side mapping');
        if (!rows) throw new Error('Table has no rows');

        // 1. Zod-like Schema (has .parse method)
        if (typeof (schemaCls as any).parse === 'function') {
            return rows.map((row: any) => {
                const rawObj: any = {};
                row.forEach((v: string, i: number) => {
                    if (headers && headers[i]) {
                        rawObj[headers[i]] = v;
                    }
                });
                return (schemaCls as any).parse(rawObj);
            });
        }

        // 2. Object Mapping Schema
        return rows.map((row: any) => {
            const obj: any = {};
            row.forEach((v: string, i: number) => {
                const h = headers ? headers[i] : undefined;
                if (h) {
                    if (schemaCls[h] && typeof schemaCls[h] === 'function') {
                        obj[h] = schemaCls[h](v);
                    } else {
                        obj[h] = v;
                    }
                }
            });
            return obj;
        });
    }

    // Return null to indicate fallthrough to WASM backend
    return null;
}
