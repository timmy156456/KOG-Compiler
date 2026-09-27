*This repo is a learning project for me. I am not accepting outside contributions or pull requests.*


# Variables and Types
var = value

OR

value = var


Forwards and backwards assignment. If you want to assign x to y as y = x (backwards assigned) then you need to write it as "(x) = y".

Variable types are determined at compile-time by the value that it is assigned.

x = 5

10 = x

These are int variables

x = true

x = False

x = TRUE

These are all examples of ways to write a boolean, caps doesn't matter.

~This is a full line comment

\~This is a block comment, a newline character is appended to the end of this so it can also serve as an optional line terminator\~

Example:
x = 5 ~~ y = x

Booleans (bools) are treated as numbers, 1 for true, -1 for false.

x = 5 * false ~x's value is -5 because 5 * -1 is -5


# Operators
Unary operators:

"-" this negates a value

"+" this makes a value its absolute value

Regular operators:

x + y ~addition

x - y ~subtraction

x * y ~multiplication

x ^ y ~exponentiation

x // y ~int division, must be used by int variable types and currently only supports positive numbers

x % y ~modulos

Boolean operators:

"==" checks if two values are equal

"!=" OR "!" checks if two values are not equal, both mean the same thing

"<" checks if left is less than right value

">" checks if left is more than right value

"<=" checks if left is less than or equal to right value

">=" checks if left is more than or equal to right value


# While Loops
while condition
    body
end

Example:
i = 0
while i < 5
    print(i)
    i = i + 1
end


# Creating and Using Functions
def returnType functionName(parameterType parameterName)
    body
    return ~every function MUST end with a return statement, but they dont all have to return something

Examples:
def int sum(int x, int y) ~creates a function with an int return type and two int parameters
    summed = x + y
    return summed

x = 5
def none increment() ~creates a function with no return type and no parameters
    x = x + 1
    return ~dont have to return a value here

Functions can only return one item at a time.
Functions can be called by putting parenthesis after the functions name, and values inside of those parenthesis.
z = add(1, 2)


# Premade Functions

print(param, param, param) ~takes infinite arguments, no newline character printed after regular arguments
println(param, param, param) ~takes infinite arguments, newline character printed after regular arguments

strint(value) ~turns a string into an integer, errors with code 127 if impossible
intput(bufferSize) ~takes an integer input of size bufferSize, I recommend using a bufferSize of 7, so you can guarantee there will be a null terminator at the end of the input

strlen(string) ~returns the length of a string, not very useful yet since strings dont exist right now

exit(code?) ~exits the program with given code value, if code value is not provided it will default to 0



# Notes
This is my first compiler.
I worked on this solo.
No AI was used to write any code at all, including the assembly.
All assembly written in the file is my own work.

I do not have strings, floats, or classes in the language yet.

# How to Use

It can read from any file, but I use .kog as the file suffix.

Until I add terminal usage, you must scroll to the very end of the file and replace the file paths with your own file path and destination.
After you have your paths in, just run the file and it will write into a .s (assembly) file.
The assembly file must exist prior to running the script or nothing will be written.
You can run the assembly file by running "./file.s" in your terminal, or by using a plugin with VSCode.
