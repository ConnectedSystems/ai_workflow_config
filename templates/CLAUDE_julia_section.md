## Julia Guidelines

- Package ops: use `pkg_add` / `pkg_rm` via Kaimon — not bare `julia -e 'Pkg.add(...)'`
- Generated code must include explicit type annotations on function signatures
- Test generation via `nim-write`: request `@testset` / `@test` and pass an existing test file as `--context`
- Prefer `using` over `import` unless selective imports are needed for disambiguation
- Numeric/scientific code: pass an existing `.jl` file as `nim-write --context` to match type annotation conventions

