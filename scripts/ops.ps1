param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

python "$PSScriptRoot\ops.py" @Args
