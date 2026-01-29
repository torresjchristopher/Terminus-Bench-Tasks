#include "common.h"
#include <iostream>

int main() {
    // Test StringProcessor
    std::string test = "Hello, World!";
    std::cout << "Original: " << test << std::endl;
    std::cout << "Reversed: " << utils::StringProcessor::reverse(test) << std::endl;

    std::vector<std::string> words = utils::StringProcessor::split("one,two,three", ',');
    std::cout << "Split result: " << utils::StringProcessor::join(words, " | ") << std::endl;

    // Test MathHelper
    std::cout << "\nFibonacci(10): " << utils::MathHelper::fibonacci(10) << std::endl;
    std::cout << "Is 17 prime? " << (utils::MathHelper::isPrime(17) ? "Yes" : "No") << std::endl;
    std::cout << "GCD(48, 18): " << utils::MathHelper::gcd(48, 18) << std::endl;

    return 0;
}
