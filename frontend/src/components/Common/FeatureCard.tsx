import {
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  Heading,
  Text,
  Button,
  Icon,
  CardRootProps,
} from "@chakra-ui/react";
import { CloseButton } from "../ui/close-button";
import { Link } from "@tanstack/react-router";
import { FiArrowRight } from "react-icons/fi";
import { IconType } from "react-icons/lib";

interface FeatureCardProps extends CardRootProps {
  title: string;
  description: string;
  icon: IconType;
  linkTo: string;
  buttonText: string;
  colorScheme?: string;
}

export const FeatureCard = ({
  title,
  description,
  icon,
  linkTo,
  buttonText,
  colorScheme = "teal",
}: FeatureCardProps) => {
  return (
    <FeatureCard
      borderRadius="lg"
      boxShadow="md"
      transition="all 0.2s"
      _hover={{
        transform: "translateY(-5px)",
        boxShadow: "lg",
      }}
    >
      <CardHeader>
        <Heading size="md">{title}</Heading>
      </CardHeader>
      <CardBody>
        <Icon as={icon} boxSize={8} mb={4} color={`${colorScheme}.500`} />
        <Text>{description}</Text>
      </CardBody>
      <CardFooter>
        <Button
          // rightIcon={<FiArrowRight />}
          colorScheme={colorScheme}
          variant="outline"
          as={Link}
          to={linkTo}
        >
          {buttonText}
        </Button>
        <CloseButton></CloseButton>
      </CardFooter>
    </FeatureCard>
  );
};
