package org.apposed.jgo.test;

/**
 * Simple test program for jgo integration tests.
 * Can be used to test basic execution, JVM args, and application args.
 */
public class HelloWorld {
    public static void main(String[] args) {
        // Print a simple message
        System.out.println("Hello, World!");

        // Print all command-line arguments (useful for testing arg passing)
        if (args.length > 0) {
            System.out.println("Arguments received: " + args.length);
            for (int i = 0; i < args.length; i++) {
                System.out.println("  arg[" + i + "]: " + args[i]);
            }
        }

        // Print a system property if requested (useful for testing JVM args)
        String testProp = System.getProperty("jgo.test.property");
        if (testProp != null) {
            System.out.println("System property jgo.test.property: " + testProp);
        }
    }
}
